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

Without a connected model the app stays offline: complete_json returns the caller's deterministic ``fixture`` marked
``"is_synthetic": True`` (never presented as model output), or raises LLMUnavailable when there is none.
"""
from __future__ import annotations

import copy
import ipaddress
import json
import logging
import os
import socket
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

try:  # .env support is optional
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

log = logging.getLogger(__name__)

PROVIDERS = {"anthropic": "Claude (Anthropic)", "openai": "OpenAI, Codex or a compatible / local model"}
DEFAULT_MODELS = {"anthropic": "claude-opus-5-5", "openai": "gpt-5"}
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
        return f"{PROVIDERS.get(self.provider, self.provider)} · {self.model or DEFAULT_MODELS.get(self.provider, '')}"


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


# ------------------------------------------------------------------ calling the model

def complete_json(prompt: str, schema: dict, fixture: Optional[dict] = None) -> dict:
    """Return a dict matching `schema`, with an added boolean "is_synthetic"."""
    cfg = active_config()
    if cfg is None:
        if fixture is None:
            raise LLMUnavailable("No model is connected and there is no demo fixture for this call.")
        return {**copy.deepcopy(fixture), "is_synthetic": True}

    last_error: Exception | None = None
    for _attempt in range(2):  # 1 retry on bad JSON
        text = _call_claude(prompt, schema) if cfg.provider == "anthropic" else _call_openai(prompt, schema)
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
    try:
        if config.provider == "openai":
            validate_base_url(config.base_url or DEFAULT_BASE_URL)
            if not config.api_key and not _is_local(config.base_url):
                return False, "Enter an API key (only a model on this machine can be used without one)."
        prompt = 'Reply with the JSON object {"ok": true}.'
        text = (_call_claude(prompt, _PING_SCHEMA, config) if config.provider == "anthropic"
                else _call_openai(prompt, _PING_SCHEMA, config))
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
