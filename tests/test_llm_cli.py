"""The local command-line providers (Claude Code, Codex): gating, the exact command that is run, and parsing."""
import json
import os
import subprocess
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from busfactor import database as db
from busfactor import llm_provider as lp
from busfactor.interview import PROMPT_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}


@pytest.fixture(autouse=True)
def clean(monkeypatch, tmp_path):
    for name in ("LLM_API_KEY", "LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL", "BUSFACTOR_ENABLE_LOCAL_CLI"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DEMO_MODE", "true")
    db.set_db_path(tmp_path / "cli.db")            # the app tests must never touch the repository's own busfactor.db
    lp.set_session_config(None)
    monkeypatch.setattr(lp.shutil, "which", lambda name: f"/fake/bin/{name}" if name in ("claude", "codex") else None)
    yield
    lp.set_session_config(None)


def completed(stdout="", returncode=0, stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


# ------------------------------------------------------------------ off unless switched on

def test_cli_providers_are_off_by_default_even_when_installed():
    assert set(lp.available_providers()) == {"anthropic", "openai"}
    assert lp.test_connection(lp.Config("claude-cli")) == (False, "The command-line providers are switched off (set BUSFACTOR_ENABLE_LOCAL_CLI=true on your own computer).")
    lp.set_session_config(lp.Config("codex-cli"))
    with pytest.raises(lp.LLMUnavailable, match="switched off"):
        lp.complete_json("q", SCHEMA)


def test_enabled_providers_appear_only_when_the_tool_is_installed(monkeypatch):
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    assert set(lp.available_providers()) == {"anthropic", "openai", "claude-cli", "codex-cli"}
    monkeypatch.setattr(lp.shutil, "which", lambda name: "/fake/bin/claude" if name == "claude" else None)
    assert set(lp.available_providers()) == {"anthropic", "openai", "claude-cli"}
    assert lp.test_connection(lp.Config("codex-cli")) == (False, "codex is not installed on this computer.")


def test_the_server_environment_can_select_a_cli_provider_only_when_enabled(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("LLM_PROVIDER", "claude-cli")
    assert lp.env_config() is None
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    cfg = lp.env_config()
    assert cfg and cfg.provider == "claude-cli" and cfg.api_key == ""


# ------------------------------------------------------------------ Claude Code

def test_claude_code_runs_with_every_tool_off_and_the_prompt_on_stdin(monkeypatch):
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-leak")
    monkeypatch.setenv("LLM_API_KEY", "sk-should-not-leak-either")
    seen = {}

    def fake_run(command, **kwargs):
        seen.update(command=command, kwargs=kwargs, cwd_existed=os.path.isdir(kwargs["cwd"]))
        events = [{"type": "system"}, {"type": "assistant"},
                  {"type": "result", "is_error": False, "result": '{"ok":true}', "structured_output": {"ok": True}}]
        return completed(json.dumps(events))
    monkeypatch.setattr(lp.subprocess, "run", fake_run)
    lp.set_session_config(lp.Config("claude-cli", model="claude-sonnet-5-5"))
    out = lp.complete_json("Reply with ok.", SCHEMA)
    assert out == {"ok": True, "is_synthetic": False}
    command, kwargs = seen["command"], seen["kwargs"]
    assert command[0] == "/fake/bin/claude" and command[1] == "-p"
    assert command[command.index("--tools") + 1] == ""                          # no tools at all
    assert command[command.index("--setting-sources") + 1] == ""                # no user or project settings, hooks or plugins
    assert "--no-session-persistence" in command and "--disable-slash-commands" in command
    assert command[command.index("--model") + 1] == "claude-sonnet-5-5"
    assert json.loads(command[command.index("--json-schema") + 1])["additionalProperties"] is False
    assert "Reply with ok." not in " ".join(command)                            # the prompt (untrusted text) is not an argument
    assert kwargs["input"] == "Reply with ok." and kwargs["shell"] is False and kwargs["timeout"] == lp.CLI_TIMEOUT_S
    assert seen["cwd_existed"] and not os.path.exists(kwargs["cwd"])            # a throw-away working directory, removed afterwards
    assert "ANTHROPIC_API_KEY" not in kwargs["env"] and "LLM_API_KEY" not in kwargs["env"]


@pytest.mark.parametrize("payload,expected", [
    ([{"type": "result", "is_error": False, "result": '{"prompt": "Why?"}'}], {"prompt": "Why?"}),            # no structured_output
    ({"type": "result", "is_error": False, "result": "", "structured_output": {"prompt": "Why?"}}, {"prompt": "Why?"}),   # old single-object form
])
def test_claude_code_output_formats_are_both_understood(monkeypatch, payload, expected):
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    monkeypatch.setattr(lp.subprocess, "run", lambda command, **k: completed(json.dumps(payload)))
    lp.set_session_config(lp.Config("claude-cli"))
    assert lp.complete_json("q", PROMPT_SCHEMA) == {**expected, "is_synthetic": False}


@pytest.mark.parametrize("stdout,returncode,stderr,words", [
    (json.dumps([{"type": "result", "is_error": True, "result": "Please login: not authenticated"}]), 1, "", "not logged in"),
    (json.dumps([{"type": "result", "is_error": True, "result": "overloaded"}]), 1, "", "reported an error"),
    ("not json at all", 0, "", "not JSON"),
    ("[]", 0, "", "no result"),
    ("", 2, "boom", r"failed \(exit 2\)"),
])
def test_claude_code_problems_become_readable_errors(monkeypatch, stdout, returncode, stderr, words):
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    monkeypatch.setattr(lp.subprocess, "run", lambda command, **k: completed(stdout, returncode, stderr))
    lp.set_session_config(lp.Config("claude-cli"))
    with pytest.raises(lp.LLMUnavailable, match=words):
        lp.complete_json("q", SCHEMA)


def test_a_tool_that_hangs_or_cannot_start_is_a_clean_error(monkeypatch):
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    lp.set_session_config(lp.Config("claude-cli"))

    def hang(command, **k):
        raise subprocess.TimeoutExpired(command, 1)
    monkeypatch.setattr(lp.subprocess, "run", hang)
    with pytest.raises(lp.LLMUnavailable, match="too long"):
        lp.complete_json("q", SCHEMA)

    def missing(command, **k):
        raise FileNotFoundError("gone")
    monkeypatch.setattr(lp.subprocess, "run", missing)
    with pytest.raises(lp.LLMUnavailable, match="could not be started"):
        lp.complete_json("q", SCHEMA)


# ------------------------------------------------------------------ Codex

def test_codex_runs_ephemeral_in_a_read_only_sandbox_and_returns_the_last_message(monkeypatch):
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    seen = {}

    def fake_run(command, **kwargs):
        seen.update(command=command, kwargs=kwargs)
        out = Path(command[command.index("--output-last-message") + 1])
        seen["schema"] = json.loads(Path(command[command.index("--output-schema") + 1]).read_text(encoding="utf-8"))
        out.write_text('{"ok": true}\n', encoding="utf-8")
        return completed("log noise", 0)
    monkeypatch.setattr(lp.subprocess, "run", fake_run)
    lp.set_session_config(lp.Config("codex-cli", model="gpt-5-codex"))
    assert lp.complete_json("Reply with ok.", SCHEMA) == {"ok": True, "is_synthetic": False}
    command = seen["command"]
    assert command[:2] == ["/fake/bin/codex", "exec"] and command[-1] == "-"          # the prompt comes on stdin
    assert command[command.index("--sandbox") + 1] == "read-only"
    for flag in ("--ephemeral", "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check"):
        assert flag in command
    assert command[command.index("--model") + 1] == "gpt-5-codex"
    assert seen["schema"]["additionalProperties"] is False
    assert seen["kwargs"]["input"] == "Reply with ok." and seen["kwargs"]["shell"] is False
    assert "Reply with ok." not in " ".join(command)


def test_codex_without_an_answer_file_is_an_error(monkeypatch):
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    monkeypatch.setattr(lp.subprocess, "run", lambda command, **k: completed("", 1, "not logged in"))
    lp.set_session_config(lp.Config("codex-cli"))
    with pytest.raises(lp.LLMUnavailable, match="Codex failed"):
        lp.complete_json("q", SCHEMA)


def test_the_connection_test_works_for_both_cli_providers(monkeypatch):
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    monkeypatch.setattr(lp, "_call_cli", lambda prompt, schema, config=None: '{"ok": true}')
    assert lp.test_connection(lp.Config("claude-cli")) == (True, "Connected.")
    assert lp.test_connection(lp.Config("codex-cli")) == (True, "Connected.")
    assert "Claude Code on this computer" in lp.Config("claude-cli").label and not lp.Config("claude-cli").label.endswith("· ")


# ------------------------------------------------------------------ the panel

def test_the_sidebar_offers_a_cli_provider_without_a_key_field(monkeypatch):
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    monkeypatch.setattr(lp, "test_connection", lambda cfg: (True, "Connected."))
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    assert any("Claude Code on this computer" in o for o in at.sidebar.selectbox(key="llm-provider").options)
    assert at.sidebar.selectbox(key="llm-provider").value == "claude-cli"              # installed tool is offered first
    at.sidebar.selectbox(key="llm-provider").set_value("anthropic")
    at.run()
    assert any(t.key == "llm-key" for t in at.sidebar.text_input)                      # an API provider still asks for a key
    at.sidebar.selectbox(key="llm-provider").set_value("claude-cli")
    at.run()
    assert not any(t.key == "llm-key" for t in at.sidebar.text_input)                  # nothing to type for a CLI
    assert any("no key is typed here" in c.value for c in at.sidebar.caption)
    at.sidebar.checkbox(key="llm-consent").check()
    at.run()
    at.sidebar.button(key="llm-connect").click()
    at.run()
    assert not at.exception, at.exception
    assert at.session_state["llm"].provider == "claude-cli"


def test_codex_shows_the_file_reading_warning(monkeypatch):
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    at.sidebar.selectbox(key="llm-provider").set_value("codex-cli")
    at.run()
    assert any("can still read files" in w.value for w in at.sidebar.warning)


def test_the_panel_explains_how_to_unlock_an_installed_tool_and_prefers_it_once_enabled(monkeypatch):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    assert any("BUSFACTOR_ENABLE_LOCAL_CLI=true" in i.value for i in at.sidebar.info)         # installed but switched off: say how
    assert not any("CLI" in o and "computer" in o for o in at.sidebar.selectbox(key="llm-provider").options)
    monkeypatch.setenv("BUSFACTOR_ENABLE_LOCAL_CLI", "true")
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    assert at.sidebar.selectbox(key="llm-provider").value == "claude-cli"                      # offered first: no key needed
    assert any("no key needed" in c.value for c in at.sidebar.caption)
    assert not any(t.key == "llm-key" for t in at.sidebar.text_input)
