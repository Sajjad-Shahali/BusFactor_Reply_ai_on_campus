"""Connecting a model for one session: providers, safety of the base URL, isolation between sessions, question source."""
import io
import ipaddress
import json
import threading
import urllib.error
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from busfactor import database as db
from busfactor import llm_provider as lp
from busfactor import orchestrator as orc
from busfactor.interview import PROMPT_SCHEMA, create_interview, create_transfer_test
from busfactor.models import DecisionCard

ROOT = Path(__file__).resolve().parents[1]
KEY = "sk-test-secret-1234567890"


@pytest.fixture(autouse=True)
def clean(monkeypatch, tmp_path):
    for name in ("LLM_API_KEY", "LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DEMO_MODE", "true")
    lp.set_session_config(None)
    db.set_db_path(tmp_path / "llm.db")
    orc.seed_demo_data()
    # DNS: api.openai.com is public, example.test resolves to a private address, metadata is link-local
    table = {"api.openai.com": "104.18.7.192", "private.test": "10.0.0.5", "metadata.test": "169.254.169.254",
             "localhost": "127.0.0.1", "127.0.0.1": "127.0.0.1"}

    def fake_getaddrinfo(host, port, *a, **k):
        try:
            ipaddress.ip_address(host)          # an IP literal resolves to itself, as in the real resolver
            return [(2, 1, 6, "", (host, port or 0))]
        except ValueError:
            pass
        if host not in table:
            raise OSError("no such host")
        return [(2, 1, 6, "", (table[host], port or 0))]
    monkeypatch.setattr(lp.socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(lp.socket, "gaierror", OSError)
    yield
    lp.set_session_config(None)


class FakeResponse:
    def __init__(self, payload):
        self._raw = json.dumps(payload).encode()

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def reply(content):
    return {"choices": [{"message": {"content": content}, "finish_reason": "stop"}]}


# ------------------------------------------------------------------ the key is never shown

def test_the_config_never_prints_the_key():
    cfg = lp.Config("openai", KEY, "gpt-5", "https://api.openai.com/v1")
    assert KEY not in repr(cfg) and KEY not in str(cfg) and KEY not in f"{cfg}" and cfg.label.startswith("OpenAI")


# ------------------------------------------------------------------ a user-supplied URL must not reach internal services

@pytest.mark.parametrize("url", ["http://169.254.169.254/latest", "https://metadata.test/v1", "https://private.test/v1",
                                 "ftp://api.openai.com/v1", "https://user:pw@api.openai.com/v1", "api.openai.com/v1",
                                 "https://nothing.invalid/v1", ""])
def test_unsafe_or_malformed_base_urls_are_refused(url):
    with pytest.raises(ValueError):
        lp.validate_base_url(url)


def test_public_and_local_urls_are_accepted(monkeypatch):
    assert lp.validate_base_url("https://api.openai.com/v1/") == "https://api.openai.com/v1"
    assert lp.validate_base_url("http://localhost:11434/v1") == "http://localhost:11434/v1"      # a model on this machine
    monkeypatch.setenv("BUSFACTOR_ALLOW_PRIVATE_LLM_URLS", "true")
    assert lp.validate_base_url("https://private.test/v1")                                         # opt-in for your own network
    with pytest.raises(ValueError):
        lp.validate_base_url("http://169.254.169.254/")                                            # link-local stays blocked


# ------------------------------------------------------------------ one connection per session

def test_a_session_connection_overrides_demo_mode_only_for_that_session():
    cfg = lp.Config("openai", KEY, "gpt-5")
    assert lp.demo_mode() and not lp.llm_available()
    seen = {}
    ready, go = threading.Barrier(2), threading.Barrier(2)

    def connected_session():
        lp.set_session_config(cfg)
        ready.wait()
        seen["a"] = (lp.llm_available(), lp.demo_mode(), "this session only" in lp.describe_connection())
        go.wait()

    def offline_session():
        lp.set_session_config(None)
        ready.wait()
        seen["b"] = (lp.llm_available(), lp.demo_mode())
        go.wait()

    threads = [threading.Thread(target=f) for f in (connected_session, offline_session)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert seen == {"a": (True, False, True), "b": (False, True)}


def test_the_environment_connects_the_whole_server_and_a_local_model_needs_no_key(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    assert lp.env_config() is None                                                               # nothing configured
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    cfg = lp.env_config()
    assert cfg and cfg.provider == "openai" and cfg.api_key == "" and cfg.model == "gpt-5"
    assert "set by the server" in lp.describe_connection()
    monkeypatch.setenv("DEMO_MODE", "true")
    assert lp.env_config() is None                                                               # DEMO_MODE keeps it offline


# ------------------------------------------------------------------ the OpenAI-compatible call

def test_openai_call_sends_a_json_schema_with_the_bearer_key_and_returns_the_parsed_answer(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout=None):
        seen["url"], seen["auth"] = request.full_url, request.get_header("Authorization")
        seen["body"] = json.loads(request.data)
        return FakeResponse(reply('{"prompt": "Why did the team pick PostgreSQL?"}'))
    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)
    lp.set_session_config(lp.Config("openai", KEY, "gpt-5-codex"))
    out = lp.complete_json("write a question", PROMPT_SCHEMA)
    assert out == {"prompt": "Why did the team pick PostgreSQL?", "is_synthetic": False}
    assert seen["url"] == "https://api.openai.com/v1/chat/completions" and seen["auth"] == f"Bearer {KEY}"
    assert seen["body"]["model"] == "gpt-5-codex" and seen["body"]["response_format"]["type"] == "json_schema"


def test_a_server_without_schema_support_gets_plain_json_mode(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout=None):
        body = json.loads(request.data)
        calls.append(body["response_format"]["type"])
        if body["response_format"]["type"] == "json_schema":
            raise urllib.error.HTTPError(request.full_url, 400, "Bad Request", {}, io.BytesIO(b'{"error": {"message": "response_format not supported"}}'))
        assert "JSON schema" in body["messages"][0]["content"]
        return FakeResponse(reply('{"prompt": "Local model question?"}'))
    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)
    lp.set_session_config(lp.Config("openai", "", "llama3", "http://localhost:11434/v1"))
    assert lp.complete_json("q", PROMPT_SCHEMA)["prompt"] == "Local model question?"
    assert calls == ["json_schema", "json_object"]


@pytest.mark.parametrize("status,words", [(401, "rejected the key"), (403, "rejected the key"), (429, "rate-limited"),
                                          (500, "Model API error 500")])
def test_provider_errors_become_readable_messages_without_the_key(monkeypatch, status, words):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, status, "boom", {}, io.BytesIO(json.dumps(
            {"error": {"message": f"bad key {KEY}"}}).encode()))
    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)
    lp.set_session_config(lp.Config("openai", KEY, "gpt-5"))
    with pytest.raises(lp.LLMUnavailable) as err:
        lp.complete_json("q", PROMPT_SCHEMA)
    assert words in str(err.value)
    ok, message = lp.test_connection(lp.Config("openai", KEY, "gpt-5"))
    assert not ok and KEY not in message


def test_a_dead_network_is_a_clean_error(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.URLError("no route")
    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)
    ok, message = lp.test_connection(lp.Config("openai", KEY, "gpt-5"))
    assert not ok and "Cannot reach" in message


def test_connection_test_rejects_missing_keys_and_bad_urls_without_calling_out(monkeypatch):
    monkeypatch.setattr(lp.urllib.request, "urlopen", lambda *a, **k: pytest.fail("must not call out"))
    assert lp.test_connection(lp.Config("anthropic", "", "m")) == (False, "Enter an API key.")
    assert not lp.test_connection(lp.Config("openai", "", "m", "https://api.openai.com/v1"))[0]      # key needed off-machine
    ok, message = lp.test_connection(lp.Config("openai", KEY, "m", "http://169.254.169.254/v1"))
    assert not ok and "not allowed" in message
    assert lp.test_connection(lp.Config("nope", KEY, "m")) == (False, "Unknown provider.")


def test_connection_test_succeeds_for_both_providers(monkeypatch):
    monkeypatch.setattr(lp, "_call_openai", lambda prompt, schema, config=None: '{"ok": true}')
    monkeypatch.setattr(lp, "_call_claude", lambda prompt, schema, config=None: '{"ok": true}')
    assert lp.test_connection(lp.Config("openai", KEY, "gpt-5")) == (True, "Connected.")
    assert lp.test_connection(lp.Config("anthropic", KEY, "claude-opus-5-5")) == (True, "Connected.")
    monkeypatch.setattr(lp, "_call_claude", lambda prompt, schema, config=None: "not json")
    assert lp.test_connection(lp.Config("anthropic", KEY, "m")) == (False, "The model did not return JSON.")


def test_claude_is_used_when_the_session_provider_is_anthropic(monkeypatch):
    monkeypatch.setattr(lp, "_call_claude", lambda prompt, schema, config=None: '{"prompt": "From Claude?"}')
    monkeypatch.setattr(lp, "_call_openai", lambda *a, **k: pytest.fail("wrong provider"))
    lp.set_session_config(lp.Config("anthropic", KEY, "claude-opus-5-5"))
    assert lp.complete_json("q", PROMPT_SCHEMA)["prompt"] == "From Claude?"


# ------------------------------------------------------------------ questions are written by the model when one is connected

def test_questions_say_who_wrote_them():
    d03 = db.get_record(DecisionCard, "D03")
    assert create_interview(d03, "M04", []).source == "demo_bank"                  # offline: the synthetic bank
    live = orc.create_project("Live", "", [("r.md", b"We chose PostgreSQL.")], ["Ada"])
    card = orc.add_decision(title="Use PostgreSQL", rationale="Transactions.", alternatives=["MongoDB"],
                            source_file="r.md", page=1, quote="We chose PostgreSQL.", project_id=live.id)
    assert create_interview(card.model_copy(update={"review_status": "verified"}), f"{live.id}-M01", []).source == "template"


def test_a_connected_model_writes_the_question_and_the_retest_scenario(monkeypatch):
    def fake_call(prompt, schema, config=None):
        if "changed_condition" in schema.get("properties", {}):
            return json.dumps({"prompt": "What if the traffic doubled overnight? Would you still pick this?",
                               "changed_condition": "Traffic doubles overnight.",
                               "expected_points": ["Keep the choice", "Explain the tradeoff"], "conclusion_changes": False})
        return json.dumps({"prompt": "In your own words, why this decision?"})
    monkeypatch.setattr(lp, "_call_openai", fake_call)
    lp.set_session_config(lp.Config("openai", KEY, "gpt-5"))
    d03 = db.get_record(DecisionCard, "D03")
    q = create_interview(d03, "M04", [])
    assert q.source == "model" and q.prompt == "In your own words, why this decision?"
    t = create_transfer_test(d03, q, [])
    assert t.source == "model" and t.scenario == "Traffic doubles overnight." and t.mode == "independent"
    assert t.rubric_expectations == ["Keep the choice", "Explain the tradeoff"]


def test_the_simulator_makes_no_model_call_for_its_throwaway_comparison_question(monkeypatch):
    calls = []

    def fake_call(prompt, schema, config=None):
        calls.append(sorted(schema.get("properties", {})))
        return json.dumps({"prompt": "What if the traffic doubled overnight? Would you still pick this?",
                           "changed_condition": "Traffic doubles.", "expected_points": ["a", "b"], "conclusion_changes": False})
    monkeypatch.setattr(lp, "_call_openai", fake_call)
    lp.set_session_config(lp.Config("openai", KEY, "gpt-5"))
    q = orc.start_simulator("M04")
    assert q.source == "model"
    assert all("changed_condition" in c for c in calls) and len(calls) == 1          # one call: the scenario itself


# ------------------------------------------------------------------ the panel in the app

def open_app():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


def test_connecting_from_the_sidebar_keeps_the_key_in_the_session_only(monkeypatch):
    monkeypatch.setattr(lp, "test_connection", lambda cfg: (True, "Connected."))
    at = open_app()
    assert any(e.label == "Connect a model" for e in at.sidebar.expander)
    assert at.sidebar.button(key="llm-connect").disabled                              # needs the consent box first
    at.sidebar.selectbox(key="llm-provider").set_value("openai")
    at.run()
    at.sidebar.text_input(key="llm-key").input(KEY)
    at.sidebar.text_input(key="llm-model").input("gpt-5-codex")
    at.sidebar.checkbox(key="llm-consent").check()
    at.run()
    at.sidebar.button(key="llm-connect").click()
    at.run()
    assert not at.exception, at.exception
    cfg = at.session_state["llm"]
    assert cfg.provider == "openai" and cfg.model == "gpt-5-codex" and cfg.api_key == KEY
    assert any(e.label == "Model: connected" for e in at.sidebar.expander)
    shown = " ".join([*(m.value for m in at.markdown), *(m.value for m in at.sidebar.markdown),
                      *(c.value for c in at.caption), *(c.value for c in at.sidebar.caption)])
    assert KEY not in shown and "this session only" in shown
    assert not any(t.key == "llm-key" for t in at.sidebar.text_input)                  # the key box is gone once connected
    # nothing was written to the database
    with db._connect() as con:
        dump = " ".join(str(row) for table in ("settings", "projects", "members", "log_events")
                        for row in con.execute(f"SELECT * FROM {table}"))
    assert KEY not in dump
    at.sidebar.button(key="llm-disconnect").click()
    at.run()
    assert "llm" not in at.session_state and any(e.label == "Connect a model" for e in at.sidebar.expander)


def test_a_failed_test_shows_the_message_and_connects_nothing(monkeypatch):
    monkeypatch.setattr(lp, "test_connection", lambda cfg: (False, "The provider rejected the key (401). Check it and the model name."))
    at = open_app()
    at.sidebar.text_input(key="llm-key").input("wrong-key")
    at.sidebar.checkbox(key="llm-consent").check()
    at.run()
    at.sidebar.button(key="llm-connect").click()
    at.run()
    assert "llm" not in at.session_state
    assert any("rejected the key" in e.value for e in at.sidebar.error)


# ------------------------------------------------------------------ the quick quiz

def test_the_quiz_asks_five_questions_in_a_row_and_never_touches_coverage():
    before = orc.team_coverage("P01").model_dump()
    at = open_app()
    at.sidebar.selectbox(key="viewer").set_value("M04")
    at.sidebar.radio[0].set_value("5. Defense Retest")
    at.run()
    at.button(key="quiz-start").click()
    at.run()
    seen = []
    for n in range(1, 6):
        assert any(f"Quiz: question {n} of 5" in m.value for m in at.markdown), n
        seen.append(at.text_area(key="sim-answer").label)
        at.text_area(key="sim-answer").input("I am not sure about this one.")
        at.button(key="sim-send").click()
        at.run()
        assert not at.exception, at.exception
    assert any("Quiz finished" in s.value for s in at.success)
    assert orc.team_coverage("P01").model_dump() == before
