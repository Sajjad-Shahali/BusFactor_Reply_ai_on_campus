"""The per-session call limit: a connected model cannot keep spending tokens (offline, with a fake call)."""
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from busfactor import database as db
from busfactor import llm_provider as lp

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
CFG = lp.Config(provider="anthropic", api_key="k" * 20, model="m")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    db.set_db_path(tmp_path / "budget.db")
    yield
    lp.set_session_config(None)
    lp.set_session_budget(None)


def fake(monkeypatch, replies):
    calls = []
    monkeypatch.setattr(lp, "_call_claude", lambda prompt, schema, config=None: (calls.append(1), replies.pop(0))[1])
    return calls


def test_the_limit_defaults_to_fifty_and_can_be_changed_or_removed(monkeypatch):
    monkeypatch.delenv("BUSFACTOR_MODEL_CALL_LIMIT", raising=False)
    assert lp.CallBudget().limit == 50
    monkeypatch.setenv("BUSFACTOR_MODEL_CALL_LIMIT", "7")
    assert lp.CallBudget().limit == 7
    monkeypatch.setenv("BUSFACTOR_MODEL_CALL_LIMIT", "0")
    assert not lp.CallBudget(used=10_000).exhausted                    # 0 = no limit
    monkeypatch.setenv("BUSFACTOR_MODEL_CALL_LIMIT", "oops")
    assert lp.CallBudget().limit == 50


def test_each_call_counts_and_the_last_one_falls_back_to_the_fixture(monkeypatch):
    calls = fake(monkeypatch, [json.dumps({"a": "live"})] * 5)
    lp.set_session_config(CFG)
    lp.set_session_budget(lp.CallBudget(limit=2))
    assert lp.complete_json("p", SCHEMA, fixture={"a": "template"})["a"] == "live"
    assert lp.complete_json("p", SCHEMA, fixture={"a": "template"})["a"] == "live"
    third = lp.complete_json("p", SCHEMA, fixture={"a": "template"})
    assert third == {"a": "template", "is_synthetic": True} and len(calls) == 2     # no third call was made


def test_without_a_fixture_the_error_says_what_happened(monkeypatch):
    calls = fake(monkeypatch, [])
    lp.set_session_config(CFG)
    lp.set_session_budget(lp.CallBudget(limit=1, used=1))
    with pytest.raises(lp.LLMUnavailable, match="limit of 1 model calls"):
        lp.complete_json("p", SCHEMA)
    assert calls == []


def test_a_retry_after_bad_json_uses_the_allowance_too(monkeypatch):
    calls = fake(monkeypatch, ["not json", json.dumps({"a": "ok"})])
    lp.set_session_config(CFG)
    budget = lp.CallBudget(limit=5)
    lp.set_session_budget(budget)
    assert lp.complete_json("p", SCHEMA)["a"] == "ok" and budget.used == 2 and len(calls) == 2


def test_the_sidebar_shows_the_count_and_offers_more_when_it_is_used_up():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    at.session_state["llm"] = CFG
    at.session_state["llm-budget"] = lp.CallBudget(limit=3, used=3)
    at.run()
    assert not at.exception, at.exception
    shown = " ".join(m.value for m in at.sidebar.markdown)
    assert "3 of 3 calls" in shown and any("fixed templates" in w.value for w in at.sidebar.warning)
    at.sidebar.button(key="llm-more").click()
    at.run()
    assert at.session_state["llm-budget"].used == 0 and not any(b.key == "llm-more" for b in at.sidebar.button)
    at.sidebar.button(key="llm-stop").click()
    at.run()
    assert "llm" not in at.session_state and at.session_state["llm-budget"].used == 0
