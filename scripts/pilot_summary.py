"""Summarise a pilot from the app's own database: counts per project, never answers, scores or names.

    python scripts/pilot_summary.py                      # every live project in busfactor.db
    BUSFACTOR_DB=path/to/other.db python scripts/pilot_summary.py

For each live (non-demo) project it prints the number of members, how many agreed to be assessed, decision
coverage at the start and now, single points of failure at the start and now, and missions by status. Paste the
table into your report together with the number of teams: with 2-3 teams this is an observation, not a result.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from busfactor import orchestrator as orc  # noqa: E402
from busfactor.models import DEMO_PROJECT_ID  # noqa: E402


def fraction(num: int, den: int) -> str:
    return f"{num}/{den}" + (f" ({num / den:.0%})" if den else "")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):   # Windows consoles default to a code page without arrows
        sys.stdout.reconfigure(encoding="utf-8")
    live = [p for p in orc.projects() if p.id != DEMO_PROJECT_ID]
    if not live:
        sys.exit("No live projects found. Create projects in the app first (or set BUSFACTOR_DB).")
    rows = ["| Project | Members | Consented | Coverage at start | Coverage now | SPOF start → now | Missions |",
            "|---|---|---|---|---|---|---|"]
    for p in live:
        team = orc.members(p.id)
        report, snaps = orc.team_coverage(p.id), orc.coverage_snapshots(p.id)
        base: dict = snaps[0] if snaps else {"numerator": 0, "denominator": 0, "spof": []}
        missions = Counter(m.status.value for m in orc.missions(p.id))
        rows.append(f"| {p.title} | {len(team)} | {sum(m.consent_assessment for m in team.values())} | "
                    f"{fraction(base['numerator'], base['denominator'])} | "
                    f"{fraction(report.numerator, report.denominator)} | "
                    f"{len(base.get('spof', []))} → {len(report.spof_decision_ids)} | "
                    + (", ".join(f"{k} {v}" for k, v in sorted(missions.items())) or "none") + " |")
    print("\n".join(rows))
    print(f"\nTeams: {len(live)}. Small samples show what happened, not what will happen elsewhere.")


if __name__ == "__main__":
    main()
