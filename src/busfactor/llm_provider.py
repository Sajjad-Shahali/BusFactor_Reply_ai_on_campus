"""LLM provider: the one place the app calls a language model.

complete_json(prompt, schema, fixture=None) -> dict

A model can be connected in two ways:

* **For one browser session** (the app's "Connect a model" panel): the provider, key, model and base URL live in
  that session's memory only, are never written to the database, a log or an export, and disappear on disconnect or
  when the session ends. Each session has its own connection (the config is thread-local, like the language).
* **For the whole server** with environment variables: LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, LLM_BASE_URL.

Providers:

* ``anthropic``: Claude, through the Anthropic SDK (structured JSON output).
* ``openai``: OpenAI models (including the Codex models) or any OpenAI-compatible endpoint, such as a local model
  served by Ollama or LM Studio (base URL on this machine, no key needed). Plain HTTPS, no extra dependency.
* ``claude-cli`` and ``codex-cli``: the Claude Code and Codex command-line tools already installed and logged in on
  this computer (no key is typed into the app). Disabled unless BUSFACTOR_ENABLE_LOCAL_CLI=true, because they run a
  program as the user who started the server: use them only for your own local copy of the app, never on a shared server.
  Claude Code runs with every tool switched off, no settings, hooks or slash commands, no session saved; Codex runs
  ephemeral in a read-only sandbox (an agent could still READ files on this computer).

Without a connected model the app stays offline: complete_json returns the caller's deterministic ``fixture`` marked
``"is_synthetic": True`` (never presented as model output), or raises LLMUnavailable when there is none.
"""
from __future__ import annotations

import copy
import ipaddress
import json
import logging
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

try:  # .env support is optional
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

log = logging.getLogger(__name__)

PROVIDERS = {"anthropic": "Claude (Anthropic)", "openai": "OpenAI, Codex or a compatible / local model",
             "claude-cli": "Claude Code on this computer (uses your Claude login)",
             "codex-cli": "Codex CLI on this computer (uses your Codex login)"}
CLI_PROVIDERS = {"claude-cli": "claude", "codex-cli": "codex"}          # provider -> the only program it may run
DEFAULT_MODELS = {"anthropic": "claude-opus-5-5", "openai": "gpt-5", "claude-cli": "", "codex-cli": ""}
CLI_TIMEOUT_S = 180
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = DEFAULT_MODELS["anthropic"]
TIMEOUT_S = 60
# Models that accept server-side refusal fallbacks with the "default" routing form.
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1"}
_UNSUPPORTED_SCHEMA_KEYS = {"maxItems", "minItems", "maxLength", "minLength", "minimum", "maximum"}


class LLMUnavailable(RuntimeError):
    """No live model and no fixture for this call (or the model refused / failed)."""


@dataclass(frozen=True)
class Config:
    """One model connection. The key is never shown: repr and str mask it."""

    provider: str
    api_key: str = ""
    model: str = ""
    base_url: str = ""

    def __repr__(self) -> str:
        key = f"{self.api_key[:3]}…({len(self.api_key)} chars)" if self.api_key else "none"
        return f"Config(provider={self.provider!r}, model={self.model!r}, base_url={self.base_url!r}, api_key={key})"

    __str__ = __repr__

    @property
    def label(self) -> str:
        model = self.model or DEFAULT_MODELS.get(self.provider, "")
        return PROVIDERS.get(self.provider, self.provider) + (f" · {model}" if model else "")


# ------------------------------------------------------------------ which connection is active

_session = threading.local()


def set_session_config(config: Optional[Config]) -> None:
    """Use `config` for this session's run (None clears it). Called at the start of every run."""
    _session.config = config


def get_session_config() -> Optional[Config]:
    return getattr(_session, "config", None)


def _env_flag(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes"}


def env_config() -> Optional[Config]:
    """The server-wide connection from the environment (offline when DEMO_MODE is true)."""
    if _env_flag("DEMO_MODE"):
        return None
    provider = (os.getenv("LLM_PROVIDER") or "anthropic").strip().lower()
    key, base = os.getenv("LLM_API_KEY", ""), os.getenv("LLM_BASE_URL", "")
    if provider in CLI_PROVIDERS:
        return Config(provider, "", os.getenv("LLM_MODEL", ""), "") if (local_cli_enabled() and cli_executable(provider)) else None
    if provider not in PROVIDERS or not (key or (provider == "openai" and base)):
        return None
    return Config(provider, key, os.getenv("LLM_MODEL") or DEFAULT_MODELS[provider], base)


def active_config() -> Optional[Config]:
    return get_session_config() or env_config()


def demo_mode() -> bool:
    """True while the app is offline: DEMO_MODE is set and no model was connected for this session."""
    return get_session_config() is None and _env_flag("DEMO_MODE")


def llm_available() -> bool:
    return active_config() is not None


def local_cli_enabled() -> bool:
    """The command-line providers run a program on this computer, so they are off unless explicitly enabled."""
    return _env_flag("BUSFACTOR_ENABLE_LOCAL_CLI")


def cli_executable(provider: str) -> Optional[str]:
    """Full path of the tool for a CLI provider, or None when it is not installed."""
    name = CLI_PROVIDERS.get(provider)
    return shutil.which(name) if name else None


def available_providers() -> dict[str, str]:
    """The providers the sidebar offers: the API ones always, the CLI ones only when enabled and installed."""
    return {key: label for key, label in PROVIDERS.items()
            if key not in CLI_PROVIDERS or (local_cli_enabled() and cli_executable(key))}


def describe_connection() -> str:
    """One line for the sidebar. Never contains the key."""
    cfg = active_config()
    if cfg is None:
        return "No model connected: questions and scoring run offline on the synthetic demo data."
    where = "this session only" if get_session_config() else "set by the server"
    return f"Model connected ({where}): {cfg.label}"


# ------------------------------------------------------------------ safe base URL

def validate_base_url(url: str) -> str:
    """The OpenAI-compatible endpoint a session may call. Returns the cleaned URL or raises ValueError.

    The server makes this request, so a user-supplied URL could be used to reach internal services. Only http(s) is
    allowed; link-local, private-network and cloud-metadata addresses are refused (set BUSFACTOR_ALLOW_PRIVATE_LLM_URLS=true
    for a model on your own network). A model on this machine (localhost) is allowed: that is the normal local setup.
    """
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("The base URL must start with http:// or https://.")
    if parsed.username or parsed.password:
        raise ValueError("Do not put credentials in the URL; use the key field.")
    try:
        addresses = {ipaddress.ip_address(info[4][0]) for info in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    except socket.gaierror as err:
        raise ValueError(f"Cannot resolve {parsed.hostname}.") from err
    allow_private = _env_flag("BUSFACTOR_ALLOW_PRIVATE_LLM_URLS")
    for ip in addresses:
        if ip.is_loopback:
            continue
        if ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_reserved:
            raise ValueError("That address is not allowed (link-local or reserved).")
        if ip.is_private and not allow_private:
            raise ValueError("That address is on a private network; set BUSFACTOR_ALLOW_PRIVATE_LLM_URLS=true to allow it.")
    return str(url).strip().rstrip("/")


# ------------------------------------------------------------------ how many calls one session may make

DEFAULT_CALL_LIMIT = 50


def call_limit() -> int:
    """Model calls one browser session may make (BUSFACTOR_MODEL_CALL_LIMIT, default 50; 0 means no limit)."""
    try:
        return max(0, int(os.getenv("BUSFACTOR_MODEL_CALL_LIMIT", str(DEFAULT_CALL_LIMIT))))
    except ValueError:
        return DEFAULT_CALL_LIMIT


@dataclass
class CallBudget:
    """A session's allowance of model calls. Each try counts, including a retry after bad JSON. When it is used up the
    app answers from the fixed templates, so a model left connected cannot keep spending tokens."""

    limit: int = field(default_factory=call_limit)
    used: int = 0

    @property
    def exhausted(self) -> bool:
        return self.limit > 0 and self.used >= self.limit

    def spend(self) -> None:
        self.used += 1

    def reset(self) -> None:
        self.used = 0


_budget = threading.local()


def set_session_budget(budget: Optional[CallBudget]) -> None:
    _budget.value = budget


def get_session_budget() -> Optional[CallBudget]:
    return getattr(_budget, "value", None)


# ------------------------------------------------------------------ calling the model

def complete_json(prompt: str, schema: dict, fixture: Optional[dict] = None) -> dict:
    """Return a dict matching `schema`, with an added boolean "is_synthetic"."""
    cfg = active_config()
    if cfg is None:
        if fixture is None:
            raise LLMUnavailable("No model is connected and there is no demo fixture for this call.")
        return {**copy.deepcopy(fixture), "is_synthetic": True}

    budget = get_session_budget()
    last_error: Exception | None = None
    for _attempt in range(2):  # 1 retry on bad JSON
        if budget is not None and budget.exhausted:   # allowance used up: fixed templates, no more spending
            if fixture is None:
                raise LLMUnavailable(f"The limit of {budget.limit} model calls for this session is reached. "
                                     "Fixed questions are used until you allow more calls.")
            return {**copy.deepcopy(fixture), "is_synthetic": True}
        if budget is not None:
            budget.spend()
        if cfg.provider == "anthropic":
            text = _call_claude(prompt, schema)
        elif cfg.provider == "openai":
            text = _call_openai(prompt, schema)
        else:
            text = _call_cli(prompt, schema)
        try:
            data = json.loads(text)
            if not isinstance(data, dict):
                raise ValueError("model output is not a JSON object")
            missing = [k for k in schema.get("required", []) if k not in data]
            if missing:
                raise ValueError(f"missing fields {missing}")
            check_types(data, schema)
            data["is_synthetic"] = False
            return data
        except (json.JSONDecodeError, ValueError) as err:
            last_error = err
            log.warning("Bad JSON from model, retrying: %s", err)
    raise LLMUnavailable(f"Model returned invalid JSON twice: {last_error}")


_JSON_TYPES: dict[str, Any] = {"string": str, "integer": int, "boolean": bool, "array": list, "object": dict, "number": (int, float)}


def check_types(data, schema: dict, path: str = "$") -> None:
    """Validate types and enums of model output against the schema (raises ValueError)."""
    expected = str(schema.get("type"))
    py = _JSON_TYPES.get(expected)
    if py is not None:
        bad_bool = expected in ("integer", "number") and isinstance(data, bool)
        if not isinstance(data, py) or bad_bool:
            raise ValueError(f"{path} should be {expected}")
    if "enum" in schema and data not in schema["enum"]:
        raise ValueError(f"{path} must be one of {schema['enum']}")
    if expected == "object":
        for key, sub in schema.get("properties", {}).items():
            if key in data:
                check_types(data[key], sub, f"{path}.{key}")
    if expected == "array" and "items" in schema:
        for i, item in enumerate(data):
            check_types(item, schema["items"], f"{path}[{i}]")


def _strict(schema: dict) -> dict:
    """Make a schema valid for structured outputs: closed objects, no size constraints."""
    def walk(node):
        if isinstance(node, dict):
            node = {k: walk(v) for k, v in node.items() if k not in _UNSUPPORTED_SCHEMA_KEYS}
            if node.get("type") == "object":
                node["additionalProperties"] = False
            return node
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node
    return walk(copy.deepcopy(schema))


def _need(cfg: Optional[Config]) -> Config:
    if cfg is None:
        raise LLMUnavailable("No model is connected.")
    return cfg


def _call_claude(prompt: str, schema: dict, config: Optional[Config] = None) -> str:
    import anthropic

    cfg = _need(config or active_config())
    model = cfg.model or DEFAULT_MODELS["anthropic"]
    client = anthropic.Anthropic(api_key=cfg.api_key, timeout=TIMEOUT_S, max_retries=2)
    kwargs: dict = dict(
        model=model,
        max_tokens=16000,
        output_config={"format": {"type": "json_schema", "schema": _strict(schema)}, "effort": "medium"},
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        if model in _FALLBACK_MODELS:
            # Server-side fallback: if a safety classifier declines, the API retries on another model.
            response = client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], extra_body={"fallbacks": "default"}, **kwargs
            )
        else:
            response = client.messages.create(**kwargs)
    except anthropic.AuthenticationError as err:
        raise LLMUnavailable("The provider rejected the key (401). Check it and the model name.") from err
    except anthropic.RateLimitError as err:
        raise LLMUnavailable("Model rate-limited; try again shortly.") from err
    except anthropic.APIStatusError as err:
        raise LLMUnavailable(f"Model API error {err.status_code}: {err.message}") from err
    except anthropic.APIConnectionError as err:
        raise LLMUnavailable("Cannot reach the model API (network).") from err

    if response.stop_reason == "refusal":
        raise LLMUnavailable("The model declined this request.")
    if response.stop_reason == "max_tokens":
        raise LLMUnavailable("Model output was cut off (max_tokens).")
    return next((b.text for b in response.content if b.type == "text"), "")


def _openai_post(cfg: Config, body: dict) -> dict:
    base = validate_base_url(cfg.base_url or DEFAULT_BASE_URL)
    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    request = urllib.request.Request(f"{base}/chat/completions", data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:  # noqa: S310  (scheme and host validated above)
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = ""
        try:
            detail = json.loads(err.read().decode("utf-8")).get("error", {}).get("message", "")
        except Exception:  # noqa: BLE001  (the body is only a hint for the message)
            pass
        if err.code in (401, 403):
            raise LLMUnavailable("The provider rejected the key (%d). Check it and the model name." % err.code) from err
        if err.code == 429:
            raise LLMUnavailable("Model rate-limited; try again shortly.") from err
        raise LLMUnavailable(f"Model API error {err.code}: {detail or err.reason}") from err
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        raise LLMUnavailable("Cannot reach the model API (network).") from err


def _call_openai(prompt: str, schema: dict, config: Optional[Config] = None) -> str:
    """OpenAI chat completions with a JSON schema; falls back to plain JSON mode for servers without schema support."""
    cfg = _need(config or active_config())
    model = cfg.model or DEFAULT_MODELS["openai"]
    messages = [{"role": "user", "content": prompt}]
    body = {"model": model, "messages": messages,
            "response_format": {"type": "json_schema", "json_schema": {"name": "answer", "schema": _strict(schema)}}}
    try:
        data = _openai_post(cfg, body)
    except LLMUnavailable as err:
        if "400" not in str(err) and "response_format" not in str(err).lower():
            raise
        # many local servers accept only JSON mode: describe the shape in the prompt instead
        hint = "\n\nReturn ONLY a JSON object that matches this JSON schema:\n" + json.dumps(_strict(schema))
        data = _openai_post(cfg, {"model": model, "messages": [{"role": "user", "content": prompt + hint}],
                                  "response_format": {"type": "json_object"}})
    try:
        choice = data["choices"][0]
        if choice.get("finish_reason") == "content_filter":
            raise LLMUnavailable("The model declined this request.")
        return choice["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as err:
        raise LLMUnavailable("The model API returned an unexpected response.") from err


# ------------------------------------------------------------------ local command-line tools

def _cli_env() -> dict[str, str]:
    """The environment for a CLI child: everything the tool needs to find its own login, minus this app's secrets."""
    return {k: v for k, v in os.environ.items() if k not in ("LLM_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")}


def _run_cli(command: list[str], prompt: str, cwd: str) -> subprocess.CompletedProcess:
    """Run a fixed program with the prompt on stdin: no shell, a throw-away working directory, a timeout."""
    try:
        return subprocess.run(command, input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=CLI_TIMEOUT_S, cwd=cwd, env=_cli_env(), shell=False, check=False)  # noqa: S603
    except subprocess.TimeoutExpired as err:
        raise LLMUnavailable("The command-line tool took too long to answer.") from err
    except OSError as err:
        raise LLMUnavailable("The command-line tool could not be started.") from err


def _claude_cli_text(raw: str) -> str:
    """The answer out of `claude -p --output-format json` (a list of events in new versions, one object in old ones)."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as err:
        raise LLMUnavailable("Claude Code returned something that is not JSON.") from err
    events = data if isinstance(data, list) else [data]
    result = next((e for e in reversed(events) if isinstance(e, dict) and e.get("type", "result") == "result"), None)
    if result is None:
        raise LLMUnavailable("Claude Code returned no result.")
    if result.get("is_error"):
        message = str(result.get("result") or "").strip()
        if "login" in message.lower() or "auth" in message.lower():
            raise LLMUnavailable("Claude Code is not logged in. Run `claude` once in a terminal and sign in.")
        raise LLMUnavailable(f"Claude Code reported an error: {message[:200] or 'unknown'}")
    structured = result.get("structured_output")
    return json.dumps(structured) if structured is not None else str(result.get("result") or "")


def _call_cli(prompt: str, schema: dict, config: Optional[Config] = None) -> str:
    cfg = _need(config or active_config())
    if not local_cli_enabled():
        raise LLMUnavailable("The command-line providers are switched off (set BUSFACTOR_ENABLE_LOCAL_CLI=true on your own computer).")
    exe = cli_executable(cfg.provider)
    if not exe:
        raise LLMUnavailable(f"{CLI_PROVIDERS.get(cfg.provider, cfg.provider)} is not installed on this computer.")
    with tempfile.TemporaryDirectory(prefix="busfactor-cli-") as work:
        if cfg.provider == "claude-cli":
            command = [exe, "-p", "--output-format", "json", "--max-turns", "2", "--tools", "",
                       "--no-session-persistence", "--setting-sources", "", "--disable-slash-commands",
                       "--json-schema", json.dumps(_strict(schema))]
            if cfg.model:
                command += ["--model", cfg.model]
            done = _run_cli(command, prompt, work)
            if done.returncode != 0 and not done.stdout.strip():
                raise LLMUnavailable(f"Claude Code failed (exit {done.returncode}): {done.stderr.strip()[:200]}")
            return _claude_cli_text(done.stdout)
        schema_file, answer_file = Path(work) / "schema.json", Path(work) / "answer.txt"
        schema_file.write_text(json.dumps(_strict(schema)), encoding="utf-8")
        command = [exe, "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules", "--sandbox", "read-only",
                   "--skip-git-repo-check", "--color", "never", "--output-schema", str(schema_file),
                   "--output-last-message", str(answer_file)]
        if cfg.model:
            command += ["--model", cfg.model]
        done = _run_cli(command + ["-"], prompt, work)
        if not answer_file.exists():
            raise LLMUnavailable(f"Codex failed (exit {done.returncode}): {(done.stderr or done.stdout).strip()[-200:]}")
        return answer_file.read_text(encoding="utf-8").strip()


# ------------------------------------------------------------------ try a connection before using it

_PING_SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}


def _redact(message: str, config: Config) -> str:
    """Never let the key come back in a message, even if a provider echoes part of it."""
    return message.replace(config.api_key, "[key]") if config.api_key else message


def test_connection(config: Config) -> tuple[bool, str]:
    """One tiny request with `config`. Returns (works, message). Never raises and never echoes the key."""
    if config.provider not in PROVIDERS:
        return False, "Unknown provider."
    if config.provider == "anthropic" and not config.api_key:
        return False, "Enter an API key."
    if config.provider in CLI_PROVIDERS:
        if not local_cli_enabled():
            return False, "The command-line providers are switched off (set BUSFACTOR_ENABLE_LOCAL_CLI=true on your own computer)."
        if not cli_executable(config.provider):
            return False, f"{CLI_PROVIDERS[config.provider]} is not installed on this computer."
    try:
        if config.provider == "openai":
            validate_base_url(config.base_url or DEFAULT_BASE_URL)
            if not config.api_key and not _is_local(config.base_url):
                return False, "Enter an API key (only a model on this machine can be used without one)."
        prompt = 'Reply with the JSON object {"ok": true}.'
        if config.provider == "anthropic":
            text = _call_claude(prompt, _PING_SCHEMA, config)
        elif config.provider == "openai":
            text = _call_openai(prompt, _PING_SCHEMA, config)
        else:
            text = _call_cli(prompt, _PING_SCHEMA, config)
        json.loads(text)
    except LLMUnavailable as err:
        return False, _redact(str(err), config)
    except json.JSONDecodeError:
        return False, "The model did not return JSON."
    except ValueError as err:   # a refused or unreachable base URL
        return False, _redact(str(err), config)
    except Exception:  # noqa: BLE001  (a connection test must never crash the page or leak the key)
        return False, "The connection test failed."
    return True, "Connected."


def _is_local(url: str) -> bool:
    host = urlparse(url or "").hostname or ""
    return host in ("localhost", "127.0.0.1", "::1")
