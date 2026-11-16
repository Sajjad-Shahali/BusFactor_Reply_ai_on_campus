"""Check that a model can be connected and that the app's model features work.

    python scripts/check_model.py                         # auto-detect what is available on this computer
    python scripts/check_model.py --provider claude-cli   # Claude Code installed and logged in on this computer
    python scripts/check_model.py --provider codex-cli    # Codex CLI installed and logged in on this computer
    python scripts/check_model.py --provider anthropic    # key from ANTHROPIC_API_KEY (or --key)
    python scripts/check_model.py --provider openai       # key from OPENAI_API_KEY; add --base-url for a local model

Steps: 1) connection test, 2) a model-written question for the demo decision D03, 3) a model-written retest scenario,
4) model scoring of a strong and a weak answer. It makes a handful of small requests (a few cents on a paid API; the CLI
tools count against their own plan). The key is never printed. Exit code 0 means every step worked.
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from busfactor import llm_provider as lp  # noqa: E402
from busfactor.interview import create_interview, create_transfer_test  # noqa: E402
from busfactor.knowledge import load_demo_decisions  # noqa: E402
from busfactor.rubrics import evaluate_answer  # noqa: E402

STRONG = ("Only about 12% of the images show a finding, so the classes are imbalanced. Always predicting no finding gives "
          "about 88% accuracy while detecting nothing, which makes accuracy misleading. F1 uses precision and recall of "
          "the positive class, so it only rises when findings are actually found.")
WEAK = "Because F1 is a better metric in general."


def detect() -> list[lp.Config]:
    """Every connection that could work on this computer right now (nothing is called yet)."""
    found: list[lp.Config] = []
    if os.getenv("ANTHROPIC_API_KEY"):
        found.append(lp.Config("anthropic", os.environ["ANTHROPIC_API_KEY"], lp.DEFAULT_MODELS["anthropic"]))
    if os.getenv("OPENAI_API_KEY"):
        found.append(lp.Config("openai", os.environ["OPENAI_API_KEY"], lp.DEFAULT_MODELS["openai"], os.getenv("OPENAI_BASE_URL", "")))
    for url in ("http://localhost:11434/v1", "http://localhost:1234/v1"):       # Ollama, LM Studio
        try:
            urllib.request.urlopen(url + "/models", timeout=2)  # noqa: S310
            found.append(lp.Config("openai", "", "", url))
        except Exception:  # noqa: BLE001, S110  (nothing listening is the normal case)
            pass
    for provider in lp.CLI_PROVIDERS:
        if lp.cli_executable(provider):
            found.append(lp.Config(provider))
    return found


def step(number: int, title: str) -> None:
    print(f"\n[{number}] {title}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", choices=sorted(lp.PROVIDERS))
    parser.add_argument("--key", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--base-url", default="")
    args = parser.parse_args()

    if args.provider in lp.CLI_PROVIDERS or (not args.provider):
        os.environ.setdefault("BUSFACTOR_ENABLE_LOCAL_CLI", "true")        # choosing a CLI here is the explicit opt-in
    if args.provider:
        key = args.key or os.getenv({"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}.get(args.provider, ""), "")
        config = lp.Config(args.provider, key, args.model or lp.DEFAULT_MODELS[args.provider], args.base_url)
    else:
        candidates = detect()
        print("Found on this computer:", ", ".join(c.label for c in candidates) or "nothing")
        if not candidates:
            print("\nNo API key, local model server or installed CLI was found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY, start "
                  "Ollama, or install and sign in to Claude Code / Codex, then run this again.")
            return 1
        config = candidates[0]
    print(f"Testing: {config.label}")

    step(1, "Connection test")
    ok, message = lp.test_connection(config)
    print(("OK: " if ok else "FAILED: ") + message)
    if not ok:
        return 1
    lp.set_session_config(config)

    decision = next(d for d in load_demo_decisions() if d.id == "D03")
    failures = 0
    step(2, "Model-written question (D03)")
    try:
        question = create_interview(decision, "M04", [])
        print(f"source: {question.source}\n{question.prompt}")
        failures += question.source != "model"
    except Exception as err:  # noqa: BLE001
        print("FAILED:", err)
        return 1
    step(3, "Model-written retest scenario (D03)")
    try:
        transfer = create_transfer_test(decision, question, [])
        print(f"source: {transfer.source}\nscenario: {transfer.scenario}\n{transfer.prompt}")
        for point in transfer.rubric_expectations:
            print(" - expected:", point)
        failures += transfer.source != "model"
    except Exception as err:  # noqa: BLE001
        print("FAILED:", err)
        return 1
    step(4, "Model scoring")
    for label, answer in (("strong answer", STRONG), ("weak answer", WEAK)):
        try:
            evidence = evaluate_answer(question, answer, decision)
            print(f"{label}: score {evidence.rubric_score}/2 ({evidence.status.value}) - {evidence.feedback[:140]}")
        except Exception as err:  # noqa: BLE001
            print(f"{label}: FAILED:", err)
            failures += 1
    print("\nAll steps worked." if not failures else f"\n{failures} step(s) did not behave as expected.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
