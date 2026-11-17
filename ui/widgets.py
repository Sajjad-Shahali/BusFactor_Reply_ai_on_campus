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

from busfactor import llm_provider
from busfactor import orchestrator as orc
from busfactor.i18n import t
from busfactor.models import MissionStatus
from ui import palettes
from ui.state import ctx
from ui.theme import PAGES

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
            st.info(t("This project has no members yet. Add the team in **1. Project Setup** first."))
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


PILL_TIPS = {
    "Only 1 can explain it": "Only one member has shown they can explain this decision. If they are absent, nobody can defend it.",
    "2+ can explain it": "At least two members have shown they can explain this decision, so the team does not depend on one person.",
    "Nobody can explain it yet": "Members were checked, but nobody has shown they can explain this decision yet.",
    "Not assessed": "Nobody has answered a question on this decision yet. That is unknown, not failed.",
    "Confirmed: can explain it": "The learner explained the decision on a new question, with no hints.",
    "Retest: try again": "The last retest answer was not complete. The learner can try a new question.",
    "Not scored: needs human review": "The grader was not sure, so a person has to look at this answer.",
}


def pill(label: str, kind: str) -> str:
    icon = f'<i class="ic{" pulse" if kind == "red" else ""}" aria-hidden="true">{PILL_ICONS.get(kind, "")}</i>'
    tip = PILL_TIPS.get(label)
    title = f' title="{esc(t(tip))}"' if tip else ""
    return f'<span class="bf-pill bf-{kind}"{title}>{icon}{esc(t(label))}</span>'


MEMBER_COLORS = [palettes.color("#4F6BFF"), "#14B8A6", "#F59E0B", "#D946EF", "#38BDF8", "#F87171"]


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
    label = esc(t("Progress: step {n} of 6").format(n=index))
    return f'<div class="bf-stepper" role="img" aria-label="{label}" title="{label}">{"".join(parts)}</div>'


def ring(num: int, den: int, base_num: int) -> str:
    """Coverage donut that animates from the baseline to the current value."""
    circ = 2 * math.pi * 62
    frac = num / den if den else 0
    start = circ * (1 - (base_num / den if den else 0))
    end = circ * (1 - frac)
    label = (f"<b>{num}/{den}</b><span>{frac:.0%} {t('covered')}</span>" if den
             else f"<b>–</b><span>{t('not measurable')}</span>")
    return (f'<div class="bf-ring" role="img" aria-label="{num}/{den}"><svg viewBox="0 0 160 160" aria-hidden="true"><defs>'
            f'<linearGradient id="bfg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{palettes.color("#7189FF")}"/>'
            f'<stop offset="1" stop-color="#2BD99F"/></linearGradient></defs>'
            f'<circle cx="80" cy="80" r="62" class="trk"/>'
            f'<circle cx="80" cy="80" r="62" class="val" style="stroke-dasharray:{circ:.1f};--from:{start:.1f};'
            f'--to:{end:.1f};stroke-dashoffset:{end:.1f}"/></svg><div class="lbl">{label}</div></div>')


def win(title: str, text: str) -> str:
    return (f'<div class="bf-win"><svg viewBox="0 0 52 52" aria-hidden="true"><circle cx="26" cy="26" r="24"/>'
            f'<path d="M15 27l7 7 15-16"/></svg><div><b>{esc(t(title))}</b><span>{esc(text)}</span></div></div>')


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
    template = palettes.recolor((ROOT / "web" / "knowledge_map.html").read_text(encoding="utf-8"))
    nodes = [{"id": c.decision_id, "title": cx.cards[c.decision_id].title, "n": len(c.demonstrated_by), "status": c.status}
             for c in report.per_decision]
    data = json.dumps({"nodes": nodes, "improved": improved}).replace("</", "<\\/")
    page_html = template.replace("__THREE__", _three_tag()).replace("__DATA__", data)
    if hasattr(st, "iframe"):   # newer Streamlit: components.html is deprecated; st.iframe also takes alt text
        st.iframe(page_html, height=height, alt=t("3D map of the decisions and who can explain them (text version below)"))
    else:
        components.html(page_html, height=height)

# ------------------------------------------------------------------ guidance: next step, Back/Next, privacy
def go_to(index: int) -> None:
    """Button callback: open page `index` (the sidebar radio is keyed "page")."""
    st.session_state["page"] = PAGES[index]


def current_page_index() -> int:
    page = st.session_state.get("page", PAGES[0])
    return PAGES.index(page) if page in PAGES else 0


def next_step_card() -> None:
    """The one most useful thing this member can do now, with a button that goes there."""
    cx = ctx()
    if cx.viewer is None:
        return
    step = orc.next_step(cx.viewer)
    text = t(step.text).format(**step.params) if step.params else t(step.text)
    label = esc(t("Your next step"))
    show(f'<div class="bf-next" role="region" aria-label="{label}"><span class="nx" aria-hidden="true">\u2192</span>'
         f'<div><b>{label}</b><span>{esc(text)}</span></div></div>')
    if current_page_index() != step.page:
        st.button(f"{t(step.button)} \u2192", key="next-step", type="primary", on_click=go_to, args=(step.page,))


def page_nav(index: int) -> None:
    """Back / Next at the bottom of a page: the way on, also on a phone where the sidebar is hidden."""
    st.divider()
    left, right = st.columns(2)
    if index > 0:
        left.button(f"\u2190 {t(PAGES[index - 1])}", key=f"nav-back-{index}", on_click=go_to, args=(index - 1,))
    if index < len(PAGES) - 1:
        right.button(f"{t(PAGES[index + 1])} \u2192", key=f"nav-next-{index}", on_click=go_to, args=(index + 1,))


def privacy_panel() -> None:
    """One place that says who can see what (privacy is the main trust question)."""
    cx = ctx()
    own = ("Only you, after you enter your access code." if cx.protected else
           "Only you (in this demo anyone can switch member, so it is synthetic data).")
    rows = [("Your answers, scores and feedback", own),
            ("Team coverage and the exports", "Everyone in the team, as counts only: no names, answers or scores."),
            ("A teaching session", "Only the mentor and the learner until both accept; then the team sees that it exists."),
            ("Answers the model could not score", "A reviewer, and only if you agreed; never with your name."),
            ("The action log", "Shared project steps and your own steps; never another member's answers.")]
    body = "".join(f"<tr><th scope='row'>{esc(t(a))}</th><td>{esc(t(b))}</td></tr>" for a, b in rows)
    with st.expander(t("Who can see what?")):
        show(f'<table class="bf-who">{body}</table>')


def draft_box(key: str, label: str, height: int = 110) -> str:
    """A text area whose draft survives moving to another page (widget state is dropped when a page is left)."""
    drafts = st.session_state.setdefault("drafts", {})
    if key not in st.session_state and key in drafts:
        st.session_state[key] = drafts[key]

    def save() -> None:
        drafts[key] = st.session_state.get(key, "")

    text = st.text_area(label, height=height, key=key, on_change=save)
    st.caption(t("Your draft is saved while you move around. After you send it, you cannot edit it."))
    return text


def clear_draft(key: str) -> None:
    st.session_state.get("drafts", {}).pop(key, None)


ACTION_TEXT = {
    "seed_demo": "The synthetic demo was loaded.",
    "create_project": "A project was created.",
    "add_member": "A member was added to the project.",
    "add_decision": "A decision card was added.",
    "confirm_card": "A decision card was confirmed.",
    "access_codes_issued": "Access codes were issued.",
    "add_course_material": "Course material was added.",
    "update_consent": "Your consent choices were saved.",
    "start_check.select_decisions": "Decisions were chosen for your private check.",
    "start_check.create_interview": "A question was prepared for you.",
    "start_check.abstain": "A decision was skipped: it is not confirmed or has no source.",
    "start_check.skip": "A decision was skipped: nothing new to ask.",
    "start_owner_check.create_interview": "A question on your own decision was prepared.",
    "submit_answer.evaluate_answer": "Your answer was recorded and assessed.",
    "submit_answer.answer_request": "A request for the answer was handled (no answer given in a check).",
    "submit_answer.flagged_instructions": "An answer addressed to the grader was not scored.",
    "propose_missions.recommend_missions": "Teaching sessions were worked out from the coverage.",
    "propose_missions.save": "Teaching sessions were saved.",
    "accept_mission": "Someone agreed to take part in a teaching session.",
    "mission_accepted": "Both people agreed to a teaching session.",
    "session_progress": "Steps of a teaching session were ticked off.",
    "start_retest.create_transfer_test": "A new retest question was prepared.",
    "submit_retest.evaluate_answer": "A retest answer was recorded and assessed.",
    "submit_retest.apply_retest": "The retest result was applied to the mission.",
    "submit_retest.blocked_answer_request": "A request for the answer was refused in the retest.",
    "submit_retest.flagged_instructions": "A retest answer addressed to the grader was not scored.",
    "start_followup": "A follow-up question was opened.",
    "start_simulator": "A defense-simulator question was prepared.",
    "submit_simulator.evaluate_answer": "A simulator answer was recorded (practice only).",
    "submit_simulator.blocked_answer_request": "A request for the answer was refused in the simulator.",
    "submit_simulator.flagged_instructions": "A simulator answer addressed to the grader was not scored.",
    "human_review": "A reviewer scored an answer.",
    "coverage_snapshot": "Team coverage was recorded.",
}


def humanize_action(action: str) -> str:
    """The action name as a plain sentence (unknown names fall back to a readable form)."""
    text = ACTION_TEXT.get(action)
    if text is None:
        text = action.replace(".", " \u2192 ").replace("_", " ").capitalize() + "."
    return t(text)



# ------------------------------------------------------------------ connect a model (this session only)
SOURCE_TEXT = {"model": "Written by the connected model", "demo_bank": "From the synthetic demo bank",
               "template": "Fixed template (no model connected)"}


def source_chip(question) -> str:
    """Who wrote a question, shown next to it so nobody mistakes a template for model output."""
    return f'<span class="bf-muted">{esc(t(SOURCE_TEXT.get(question.source, SOURCE_TEXT["template"])))}</span>'


def _connect_model() -> None:
    """Button callback: test the typed connection and, if it works, keep it for this session only."""
    state = st.session_state
    provider = state.get("llm-provider", "anthropic")
    cfg = llm_provider.Config(
        provider=provider, api_key=(state.get("llm-key") or "").strip(),
        model=(state.get("llm-model") or "").strip() or llm_provider.DEFAULT_MODELS[provider],
        base_url=(state.get("llm-base") or "").strip() if provider == "openai" else "")
    ok, message = llm_provider.test_connection(cfg)
    state["llm-msg"] = (ok, message)
    if ok:
        state["llm"] = cfg
        state["llm-key"] = ""          # the typed key does not stay in the page's input


def _disconnect_model() -> None:
    st.session_state.pop("llm", None)
    st.session_state["llm-key"] = ""
    st.session_state.pop("llm-msg", None)


def model_status() -> None:
    """Always-visible switch at the top of the sidebar: while a model is connected, one click stops using it.

    Disconnecting drops the connection from this session at once, so no further call is made (a call already running
    cannot be recalled, but its answer is the last one). The questions then fall back to the fixed templates.
    """
    cfg = llm_provider.get_session_config()
    if not cfg:
        return
    st.markdown(f'<div class="bf-muted">● {esc(t("Model on: {m}").format(m=cfg.label))}</div>', unsafe_allow_html=True)
    st.button(t("Stop the model"), key="llm-stop", on_click=_disconnect_model, type="primary", width="stretch",
              icon=":material/stop_circle:", help=t("Disconnects the model now. No more calls are sent; questions fall "
                                                   "back to the fixed templates."))


def model_panel() -> None:
    """Connect Claude, OpenAI/Codex or a local OpenAI-compatible model for THIS browser session.

    The key lives in this session's memory only (not the database, logs or exports) and is gone on Disconnect.
    """
    cfg = llm_provider.get_session_config()
    title = t("Model: connected") if cfg else t("Connect a model")
    with st.expander(title, expanded=False):
        st.caption(t(llm_provider.describe_connection()) if not cfg else
                   t("Model connected (this session only): {m}").format(m=cfg.label))
        if cfg:
            st.button(t("Disconnect"), key="llm-disconnect", on_click=_disconnect_model)
            return
        env = llm_provider.env_config()
        if env:
            st.caption(t("The server already has a model configured: {m}").format(m=env.label))
        options = llm_provider.available_providers()
        installed = [p for p in llm_provider.CLI_PROVIDERS if llm_provider.cli_executable(p)]
        if installed and not llm_provider.local_cli_enabled():
            st.info(t("Claude Code or Codex is installed on this computer. To use it without a key, start the app with "
                      "BUSFACTOR_ENABLE_LOCAL_CLI=true (your own computer only)."))
        elif installed:   # no key needed: offer the installed tool first
            st.caption(t("Claude Code / Codex found on this computer: pick it below, no key needed."))
            st.session_state.setdefault("llm-provider", installed[0])
        st.selectbox(t("Provider"), list(options), format_func=lambda p: options[p], key="llm-provider")
        provider = st.session_state.get("llm-provider", "anthropic")
        if provider in llm_provider.CLI_PROVIDERS:
            st.caption(t("Runs the tool already installed and logged in on this computer: no key is typed here. Use it "
                         "only on your own computer, never on a shared server."))
            if provider == "codex-cli":
                st.warning(t("Codex runs in a read-only sandbox, but it can still read files on this computer."))
        else:
            st.text_input(t("API key"), type="password", key="llm-key",
                          help=t("Kept in this session's memory only: not saved to the database, the logs or any export."))
        st.text_input(t("Model name"), key="llm-model",
                      placeholder=llm_provider.DEFAULT_MODELS[provider] or t("(the tool's default)"))
        if provider == "openai":
            st.text_input(t("Base URL"), key="llm-base", placeholder=llm_provider.DEFAULT_BASE_URL,
                          help=t("Leave empty for OpenAI. For a model on this computer use e.g. http://localhost:11434/v1 "
                                 "(Ollama); no key is needed then."))
        agreed = st.checkbox(t("I understand that the project text and my team's answers are sent to this provider "
                               "to write questions and score answers."), key="llm-consent")
        st.button(t("Connect and test"), key="llm-connect", type="primary", disabled=not agreed, on_click=_connect_model)
        result = st.session_state.get("llm-msg")
        if result and not result[0]:
            st.error(t(result[1]))
