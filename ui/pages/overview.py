"""Overview page: KPIs, the 3D knowledge map and the demo story."""
from __future__ import annotations


import streamlit as st

from busfactor import orchestrator as orc
from busfactor.i18n import t
from busfactor.models import MissionStatus, ReviewStatus
from ui.state import ctx
from ui.theme import (
    COVERAGE_PILL, HERO_TEXT, HERO_TITLE,
)
from ui.widgets import (
    dlabel, esc, knowledge_map, show,
)


def render() -> None:
    cx = ctx()
    report = orc.team_coverage()
    snaps = orc.coverage_snapshots()
    base = snaps[0] if snaps else {"numerator": report.numerator, "denominator": report.denominator,
                                     "spof": report.spof_decision_ids}
    status_now = {c.decision_id: c.status for c in report.per_decision}
    improved = [d for d in base.get("spof", []) if status_now.get(d) == "covered"]
    ms = orc.missions()
    accepted = [m for m in ms if m.status in (MissionStatus.accepted, MissionStatus.completed, MissionStatus.verified)]
    verified_missions = [m for m in ms if m.status == MissionStatus.verified]
    verified_cards = sum(d.review_status == ReviewStatus.verified for d in cx.cards.values())
    p = orc.project()

    gained = report.numerator - base["numerator"]
    spof_drop = len(base.get("spof", [])) - len(report.spof_decision_ids)
    kpis = [
        (t("Decision coverage"), f"{report.numerator}/{report.denominator}" if report.denominator else "–",
         t("<b>+{n}</b> since start").format(n=gained) if gained > 0
         else t("started at {a}/{b}").format(a=base["numerator"], b=base["denominator"])),
        (t("Single points of failure"), str(len(report.spof_decision_ids)),
         t("<b>−{n}</b> since start").format(n=spof_drop) if spof_drop > 0
         else t('<b class="bad">need a second explainer</b>')),
        (t("Teaching missions"), str(len(accepted)),
         t("{n} proposed · {v} verified").format(n=len(ms), v=len(verified_missions))),
        (t("Decisions verified"), f"{verified_cards}/{len(cx.cards)}", t("quotes checked on their page")),
    ]
    tiles = "".join(f'<div class="bf-kpi"><div class="k">{k}</div><div class="v">{v}</div><div class="s">{s}</div></div>'
                    for k, v, s in kpis)
    kicker = t("Synthetic demo") if orc.is_demo_project() else t("Your project")
    show(f'<div class="bf-dark"><div class="kicker">{kicker} · {esc(p.title if p else "BusFactor")}</div>'
         f'<h1>{t(HERO_TITLE)}</h1>'
         f'<p>{esc(t(HERO_TEXT))}</p>'
         f'<div class="bf-kpis">{tiles}</div></div>')

    knowledge_map(report, improved)
    text_map = "; ".join(f"{dlabel(c.decision_id)}: {t(COVERAGE_PILL[c.status][0])} ({len(c.demonstrated_by)})"
                         for c in report.per_decision)
    show(f'<div class="bf-muted" role="note">{esc(t("Text version of the map"))}: {esc(text_map)}</div>')

    steps = [
        (t("Find the decisions"), verified_cards > 0,
         t("{n} of {m} cards verified against the report").format(n=verified_cards, m=len(cx.cards))),
        (t("Ask privately"), report.denominator > 0,
         t("{n} decisions have private answers").format(n=report.denominator)),
        (t("Spot the risk"), bool(base.get("spof")),
         t("{n} decisions depended on one person").format(n=len(base.get("spof", [])))),
        (t("Teach each other"), bool(accepted), t("{n} mission(s) accepted by both people").format(n=len(accepted))),
        (t("Check again"), bool(verified_missions),
         t("{n} transfer(s) verified · coverage {a} → {b}").format(
             n=len(verified_missions), a=f"{base['numerator']}/{base['denominator']}",
             b=f"{report.numerator}/{report.denominator}")),
    ]
    first_open = next((i for i, (_, done, _) in enumerate(steps) if not done), None)
    html_steps = []
    for i, (title, done, detail) in enumerate(steps):
        cls, state = (("done", t("Done")) if done else
                      (("next", t("Up next")) if i == first_open else ("", t("Waiting"))))
        html_steps.append(f'<div class="bf-sc {cls}"><div class="n">{"✓" if done else i + 1}</div>'
                          f'<h4>{title}</h4><p>{esc(detail)}</p><div class="st">{state}</div></div>')
    st.subheader(t("Demo story"))
    show(f'<div class="bf-story">{"".join(html_steps)}</div>')
    show('<div class="bf-muted">' + t("All numbers come from the synthetic demo data and update live as you use "
                                      "the app." if orc.is_demo_project() else
                                      "All numbers come from this project's stored, consented evidence.") + '</div>')
