"""Shared UI helpers: small renderers, empty states, reminders and access-code display."""
from __future__ import annotations

import html
import json
import math
from functools import lru_cache
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from busfactor import orchestrator as orc
from busfactor.i18n import t
from busfactor.models import MissionStatus
from ui.state import ctx

ROOT = Path(__file__).resolve().parents[1]


def load_project_state() -> None:
    """(Re)load members, names, cards and labels of the open project into this session's context."""
    cx = ctx()
    cx.members = orc.members()
    cx.names = {m.id: m.display_name for m in cx.members.values()}
    cx.cards = {d.id: d for d in orc.decisions()}
    cx.labels = {**cx.names, **{did: dlabel(did) for did in cx.cards}}  # for explain_mission: people and decisions


def dlabel(decision_id: str) -> str:
    """Short decision label: live ids are <project>-D01, the demo uses D01."""
    return decision_id.rsplit("-", 1)[-1]


def need_viewer() -> None:
    cx = ctx()
    if cx.viewer is None:
        if cx.locked:
            st.info(t("Enter your access code in the sidebar to continue."))
        else:
            st.info("This project has no members yet. Add the team in **1. Project Setup** first.")
        st.stop()


def show_reminders() -> None:
    """Nudges for the signed-in member: an idle teaching session, or a follow-up check that is due."""
    cx = ctx()
    if cx.viewer is None:
        return
    for r in orc.reminders(cx.viewer):
        key = ("Reminder: the teaching session for {d} was agreed {n} days ago. Do it, then take the retest (page 5)."
               if r["kind"] == "session" else
               "Follow-up check due: you passed the retest for {d} {n} days ago. One new question shows whether "
               "it stuck.")
        st.info(t(key).format(d=dlabel(r["decision_id"]), n=r["days"]), icon="⏰")


def show_issued_codes() -> None:
    """Access codes are shown once, right after they are issued, and only in this browser session."""
    issued = st.session_state.get("issued_codes")
    if not issued or issued["project_id"] != orc.active_project_id():
        return
    with st.container(border=True):
        st.warning(t("Save these access codes now. They are shown only once and cannot be recovered."))
        rows = [{t("Member"): name, t("Access code"): code} for name, code in issued["members"].items()]
        if issued.get("reviewer"):
            rows.append({t("Member"): t("Reviewer code"), t("Access code"): issued["reviewer"]})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        if st.button(t("I have saved the codes"), key="codes-saved"):
            del st.session_state["issued_codes"]
            st.rerun()


def remember_codes(codes: dict, project_id: str, member_names: dict) -> None:
    st.session_state["issued_codes"] = {
        "project_id": project_id, "reviewer": codes.get("reviewer"),
        "members": {member_names[mid]: code for mid, code in codes["members"].items()}}


# ------------------------------------------------------------------ small UI helpers
def esc(text: object) -> str:
    return html.escape(str(text))


PILL_ICONS = {"green": "✓", "red": "▲", "amber": "◐", "blue": "●", "gray": "○", "ink": "◆"}   # shape + colour


def pill(label: str, kind: str) -> str:
    icon = f'<i class="ic{" pulse" if kind == "red" else ""}" aria-hidden="true">{PILL_ICONS.get(kind, "")}</i>'
    return f'<span class="bf-pill bf-{kind}">{icon}{esc(t(label))}</span>'


MEMBER_COLORS = ["#4F6BFF", "#14B8A6", "#F59E0B", "#D946EF", "#38BDF8", "#F87171"]


def avatar(member_id: str, size: int = 34) -> str:
    """Coloured initial for a member (colour is fixed per member id)."""
    cx = ctx()
    order = sorted(cx.names)
    color = MEMBER_COLORS[(order.index(member_id) if member_id in order else 0) % len(MEMBER_COLORS)]
    initial = cx.names.get(member_id, member_id).split()[-1][:1]
    return (f'<span class="bf-av" style="--c:{color};width:{size}px;height:{size}px;'
            f'font-size:{round(size * 0.42)}px">{esc(initial)}</span>')


STEP_SHORT = ["Setup", "Check", "Coverage", "Teach", "Retest", "Evidence"]


def stepper(index: int) -> str:
    parts = []
    for i, name in enumerate(STEP_SHORT, 1):
        if i > 1:
            parts.append(f'<i class="{"done" if i <= index else ""}"></i>')
        state = "done" if i < index else "now" if i == index else ""
        parts.append(f'<div class="bf-st {state}"><span>{"✓" if i < index else i}</span>{esc(t(name))}</div>')
    return f'<div class="bf-stepper">{"".join(parts)}</div>'


def ring(num: int, den: int, base_num: int) -> str:
    """Coverage donut that animates from the baseline to the current value."""
    circ = 2 * math.pi * 62
    frac = num / den if den else 0
    start = circ * (1 - (base_num / den if den else 0))
    end = circ * (1 - frac)
    label = (f"<b>{num}/{den}</b><span>{frac:.0%} {t('covered')}</span>" if den
             else f"<b>–</b><span>{t('not measurable')}</span>")
    return (f'<div class="bf-ring" role="img" aria-label="{num}/{den}"><svg viewBox="0 0 160 160" aria-hidden="true"><defs>'
            f'<linearGradient id="bfg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7189FF"/>'
            f'<stop offset="1" stop-color="#2BD99F"/></linearGradient></defs>'
            f'<circle cx="80" cy="80" r="62" class="trk"/>'
            f'<circle cx="80" cy="80" r="62" class="val" style="stroke-dasharray:{circ:.1f};--from:{start:.1f};'
            f'--to:{end:.1f};stroke-dashoffset:{end:.1f}"/></svg><div class="lbl">{label}</div></div>')


def win(title: str, text: str) -> str:
    return (f'<div class="bf-win"><svg viewBox="0 0 52 52" aria-hidden="true"><circle cx="26" cy="26" r="24"/>'
            f'<path d="M15 27l7 7 15-16"/></svg><div><b>{esc(title)}</b><span>{esc(text)}</span></div></div>')


def flow(m) -> str:
    """Mentor -> learner with a moving arrow; ticks show who has accepted."""
    cx = ctx()
    tick = lambda ok: '<em class="ck">✓</em>' if ok else ""  # noqa: E731
    done = "ok" if m.status == MissionStatus.verified else ""
    return (f'<div class="bf-flow">'
            f'<div class="who">{avatar(m.mentor_id, 40)}{tick(m.mentor_consent)}'
            f'<div><b>{esc(cx.names[m.mentor_id])}</b><span>{esc(t("Mentor"))}</span></div></div>'
            f'<div class="arrow {done}"><i></i></div>'
            f'<div class="who">{avatar(m.learner_id, 40)}{tick(m.learner_consent)}'
            f'<div><b>{esc(cx.names[m.learner_id])}</b><span>{esc(t("Learner"))}</span></div></div></div>')


def show(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


ICONS = {
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.4"/>'
             '<path d="M16 14.2c2.9.3 5 2.6 5 5.8"/>',
    "inbox": '<path d="M3 13l3-8h12l3 8v6H3z"/><path d="M3 13h5l1 3h6l1-3h5"/>',
    "path": '<circle cx="5" cy="18" r="2.2"/><circle cx="19" cy="6" r="2.2"/><path d="M7 18h6a3 3 0 0 0 0-6h-2a3 3 0 0 1 0-6h6"/>',
    "doc": '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4M10 12h6M10 16h6"/>',
    "shield": '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/>',
}
LOCK_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="2"/>'
            '<path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>')


def empty_state(icon: str, title: str, text: str) -> None:
    """A friendly empty page: icon, what is missing and the next action (not just an empty list)."""
    svg = (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
           f'stroke-linejoin="round" aria-hidden="true">{ICONS[icon]}</svg>')
    show(f'<div class="bf-empty" role="status">{svg}<b>{esc(t(title))}</b><span>{esc(t(text))}</span></div>')


def page_header(index: int, title: str, subtitle: str) -> None:
    head, _, tail = title.partition(" · ")
    heading = esc(t(head)) + (f" <em>· {esc(tail)}</em>" if tail else "")
    show(f'<div class="bf-hero">{stepper(index)}<h1>{heading}</h1><p>{esc(t(subtitle))}</p></div>')


def coverage_text(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return t("not measurable")
    return f"{numerator}/{denominator} ({numerator / denominator:.0%})"


def quote_block(ref) -> str:
    where = f"{esc(ref.file)} · page {ref.page}" + (f" · {esc(ref.section)}" if ref.section else "")
    return f'<div class="bf-quote">“{esc(ref.quote)}”<br><span class="bf-muted">{where}</span></div>'


@lru_cache(maxsize=1)
def _three_tag() -> str:
    """three.js from the repo (works offline at the venue); falls back to the CDN."""
    local = ROOT / "web" / "vendor" / "three.min.js"
    if local.exists():
        return "<script>" + local.read_text(encoding="utf-8").replace("</script", "<\\/script") + "</script>"
    return '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>'


def knowledge_map(report, improved: list[str], height: int = 470) -> None:
    """3D map: one node per decision, one orbiting light per person who can explain it. Counts only."""
    cx = ctx()
    template = (ROOT / "web" / "knowledge_map.html").read_text(encoding="utf-8")
    nodes = [{"id": c.decision_id, "title": cx.cards[c.decision_id].title, "n": len(c.demonstrated_by), "status": c.status}
             for c in report.per_decision]
    data = json.dumps({"nodes": nodes, "improved": improved}).replace("</", "<\\/")
    page_html = template.replace("__THREE__", _three_tag()).replace("__DATA__", data)
    if hasattr(st, "iframe"):   # newer Streamlit: components.html is deprecated; st.iframe also takes alt text
        st.iframe(page_html, height=height, alt=t("3D map of the decisions and who can explain them (text version below)"))
    else:
        components.html(page_html, height=height)
