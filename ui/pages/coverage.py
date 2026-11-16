"""Page 3: team coverage, verdict and exports (counts only)."""
from __future__ import annotations


import streamlit as st

from busfactor import orchestrator as orc
from busfactor.coverage import explain_status
from busfactor.i18n import t, tr_dynamic
from busfactor.models import ReviewStatus
from ui.state import ctx
from ui.theme import (
    COVERAGE_PILL,
)
from ui.widgets import (
    coverage_text, dlabel, esc, next_step_card, page_header, page_nav, pill, privacy_panel, ring, show,
)


def render() -> None:
    cx = ctx()
    page_header(3, "Team Coverage",
                "How many decisions at least two of you can explain. Only counts are shown, never names or scores.")
    next_step_card()
    privacy_panel()
    report = orc.team_coverage()
    snaps = orc.coverage_snapshots()
    base = snaps[0] if snaps else None

    start = base or {"numerator": report.numerator, "denominator": report.denominator, "spof": report.spof_decision_ids}
    gained = report.numerator - start["numerator"]
    spof_drop = len(start.get("spof", [])) - len(report.spof_decision_ids)
    stats = [
        (t("Since the start"),
         f'<span class="small">{esc(coverage_text(start["numerator"], start["denominator"]))} \u2192 '
         f'{esc(coverage_text(report.numerator, report.denominator))}</span>',
         (t("<b>+1</b> decision covered") if gained == 1 else t("<b>+{n}</b> decisions covered").format(n=gained))
         if gained > 0 else t("no change yet")),
        (t("Decisions only 1 person can explain"), str(len(report.spof_decision_ids)),
         t("<b>−{n}</b> since start").format(n=spof_drop) if spof_drop > 0
         else t("decisions only one person can explain")),
    ]
    tiles = "".join(f'<div><div class="k">{k}</div><div class="v{" small" if "small" in v else ""}">{v}</div>'
                    f'<div class="s">{sub}</div></div>' for k, v, sub in stats)
    n_spof = len(report.spof_decision_ids)
    if report.denominator == 0:
        vkind, vicon, vmain = "idle", "?", t("Nothing has been assessed yet.")
        vnext = t("Members can take a private check on the Private Check page.")
    elif n_spof:
        vkind, vicon = "warn", "!"
        vmain = (t("1 decision depends on one person.") if n_spof == 1
                 else t("{n} decisions depend on one person.").format(n=n_spof))
        vnext = t("Next: open Teach Each Other and propose missions.")
    else:
        vkind, vicon, vmain = "good", "✓", t("No decision depends on one person.")
        vnext = t("Keep it fresh: practise a new 'what if' before the defense.")
    show(f'<div class="bf-verdict {vkind}" role="status"><span class="vi" aria-hidden="true">{vicon}</span>'
         f'<div><b>{esc(vmain)}</b><span class="next">{esc(vnext)}</span></div></div>')
    show(f'<div class="bf-panel">{ring(report.numerator, report.denominator, start["numerator"])}'
         f'<div class="bf-pstats">{tiles}</div>'
         f'<div class="note">{esc(t("The ring fills as more decisions get a second person who can explain them."))}'
         '</div></div>')

    confirmed = [d for d in cx.cards.values() if d.review_status == ReviewStatus.verified]
    unconfirmed_note = (t(" · {n} not confirmed yet, so not counted").format(n=len(cx.cards) - len(confirmed))
                        if len(confirmed) < len(cx.cards) else "")
    show(f'<div class="bf-muted">'
         f'{esc(t("{a} of {b} confirmed decisions have been assessed").format(a=report.denominator, b=len(confirmed)))}'
         f'{esc(unconfirmed_note)}.</div>')

    st.subheader(t("Decisions"))
    team_size = len(cx.members)
    for c in report.per_decision:
        unconfirmed = cx.cards[c.decision_id].review_status != ReviewStatus.verified
        with st.container(border=True):
            label, kind = ("Not confirmed", "gray") if unconfirmed else COVERAGE_PILL[c.status]
            n = len(c.demonstrated_by)
            left, mid, right = st.columns([4.5, 1.6, 1.8])
            left.markdown(f"**{dlabel(c.decision_id)} · {cx.cards[c.decision_id].title}**")
            with mid:
                dots = "".join('<i class="on"></i>' if k < n else "<i></i>" for k in range(team_size))
                show(f'<div class="bf-dots2 {c.status}" title="{n} of {team_size}">{dots}</div>'
                     f'<span class="bf-muted">{esc(t("{n} can explain it").format(n=n))}</span>')
            with right:
                show(pill(label, kind))
            why, step = (("It is not confirmed or has no verified source, so it is not counted.",
                          "Review it in Project Setup.") if unconfirmed else explain_status(c))
            show(f'<div class="bf-muted">{esc(tr_dynamic(why))} <b>{esc(t("Next:"))}</b> {esc(tr_dynamic(step))}</div>')

    st.subheader(t("Export"))
    slug = "".join(ch if ch.isalnum() else "_" for ch in (orc.project().title if orc.project() else "team")).strip("_")
    left_dl, mid_dl, right_dl = st.columns(3)
    left_dl.download_button(t("Download team report (PDF)"), orc.export_team_report_pdf(),
                            file_name=f"busfactor_report_{slug}.pdf", mime="application/pdf", key="dl-pdf")
    mid_dl.download_button(t("Download team report (Markdown)"), orc.export_team_report(),
                           file_name=f"busfactor_report_{slug}.md", mime="text/markdown", key="dl-md")
    right_dl.download_button(t("Download decisions (CSV)"), orc.export_decisions_csv(),
                             file_name=f"busfactor_decisions_{slug}.csv", mime="text/csv", key="dl-csv")
    show(f'<div class="bf-muted">{esc(t("The exports contain counts only: no names, answers or scores."))}</div>')
    show('<div class="bf-muted" style="margin-top:0.8rem">Decision Coverage = critical decisions that 2 or more '
         'members can explain ÷ critical decisions that have been assessed. This is a prototype indicator, '
         'not a validated metric. "Not assessed" is never counted as failed.</div>')

    page_nav(3)
