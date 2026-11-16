"""Page 1: project setup, members, access codes, course material and decision cards."""
from __future__ import annotations


import streamlit as st

from busfactor import auth
from busfactor import orchestrator as orc
from busfactor.i18n import t
from busfactor.llm_provider import LLMUnavailable, llm_available
from busfactor.models import ReviewStatus
from ui.state import ctx
from ui.theme import (
    CARD_PILL,
)
from ui.widgets import (
    dlabel, empty_state, esc, page_header, page_nav, pill, quote_block, remember_codes, show, show_issued_codes,
)


def render() -> None:
    cx = ctx()
    p = orc.project()
    demo = orc.is_demo_project()
    page_header(1, p.title if p else "Project Setup",
                "The key decisions of the project. Each one is linked to the exact page it comes from.")
    if p:
        docs = ", ".join(p.source_files) or t("no document yet")
        show(f'<div class="bf-muted">{esc(p.course or t("No course given"))} · {esc(t("source"))}: {esc(docs)}</div>')

    by_status = {s: [d for d in cx.cards.values() if d.review_status == s] for s in ReviewStatus}
    if not cx.members:
        next_step = "Add the team members below. Each member then opts in to assessment on the Private Check page."
    elif not cx.cards:
        next_step = "Add the project's key decisions: by hand (each quote is checked) or with the live model."
    elif by_status[ReviewStatus.proposed]:
        next_step = (f"Review {len(by_status[ReviewStatus.proposed])} proposed decision(s): check the quote, "
                     "choose the owner, confirm. Nothing is assessed before it is confirmed.")
    else:
        next_step = "Decisions are confirmed. Members can now take private checks and owners their owner checks."
    st.info(f"**{t('Next step')}:** {t(next_step)}")

    show_issued_codes()
    with st.expander(t("Start a new project")):
        st.caption(t("A new project is added next to the existing ones; nothing is deleted. Members start with "
                     "every consent off. Only upload documents you are allowed to share."))
        with st.form("new-project"):
            new_title = st.text_input(t("Project title"))
            new_course = st.text_input(t("Course"))
            new_doc = st.file_uploader(t("Project report (PDF, Markdown or text)"), type=["pdf", "md", "txt"])
            new_names = st.text_area(t("Team members, one name per line"))
            if st.form_submit_button(t("Create project"), type="primary"):
                try:
                    made = orc.create_project(new_title, new_course,
                                              [(new_doc.name, new_doc.getvalue())] if new_doc else [],
                                              new_names.splitlines(), actor=cx.viewer or "agent")
                    if orc.members(made.id):   # a new project starts protected: every member gets a personal code
                        remember_codes(orc.protect_project(made.id), made.id,
                                       {m.id: m.display_name for m in orc.members(made.id).values()})
                    st.rerun()
                except ValueError as err:
                    st.error(str(err))

    if not demo:
        with st.container(border=True):
            st.markdown(f"**{t('Team members ({n})').format(n=len(cx.members))}**")
            show('<div class="bf-muted">' + (esc(", ".join(cx.names.values())) or esc(t("No members yet.")))
                 + " · " + esc(t("Each member opts in for themselves on the Private Check page.")) + "</div>")
            with st.form("add-member", clear_on_submit=True):
                new_member = st.text_input(t("Add a member (name)"))
                if st.form_submit_button(t("Add member")):
                    try:
                        added = orc.add_member(new_member, actor=cx.viewer or "agent")
                        if orc.is_protected():
                            st.session_state["issued_codes"] = {
                                "project_id": added.project_id, "reviewer": None,
                                "members": {added.display_name: auth.issue_member_code(added.id)}}
                        st.rerun()
                    except ValueError as err:
                        st.error(str(err))

        with st.container(border=True):
            st.markdown(f"**{t('Access codes')}**")
            if orc.is_protected():
                st.caption(t("This project uses access codes. Each member unlocks their own answers with a personal "
                             "code; the review queue needs the reviewer code."))
                with st.expander(t("Issue new codes")):
                    st.caption(t("New codes replace the old ones: everyone must unlock again. Type the project "
                                 "title to confirm."))
                    again = st.text_input(t("Type the project title to confirm"), key="recode-title")
                    if st.button(t("Issue new codes"), key="recode", disabled=again.strip() != p.title):
                        cx.unlocked.clear()
                        remember_codes(orc.protect_project(p.id), p.id,
                                       {m.id: m.display_name for m in cx.members.values()})
                        st.rerun()
            else:
                st.caption(t("Access codes are off: anyone using this app can switch to any member and read that "
                             "member's answers. Turn them on before real students use it."))
                if st.button(t("Turn on access codes"), key="codes-on", disabled=not cx.members):
                    remember_codes(orc.protect_project(p.id), p.id, {m.id: m.display_name for m in cx.members.values()})
                    st.rerun()

        with st.container(border=True):
            st.markdown(f"**{t('Course material (optional)')}**")
            st.caption(t("Lecture notes or slides of the course. When nobody can explain a decision, BusFactor points "
                         "to the page that talks about it instead of a generic message."))
            ready = orc.course_materials(p.id)
            if ready:
                show(f'<div class="bf-muted">{esc(", ".join(ready))}</div>')
            course_files = st.file_uploader(t("Add course files (PDF, Markdown or text)"), type=["pdf", "md", "txt"],
                                            accept_multiple_files=True, key="course-up")
            if st.button(t("Add course material"), key="course-add", disabled=not course_files):
                try:
                    for f in course_files:
                        orc.add_course_material(f.name, f.getvalue(), p.id)
                    st.rerun()
                except ValueError as err:
                    st.error(str(err))

        with st.container(border=True):
            st.markdown(f"**{t('Add decisions')}**")
            if not p.source_files:
                st.warning(t("This project has no document, so no decision can be source-checked. Start a new project "
                             "with its report."))
            else:
                if not cx.cards:
                    if st.button(t("Propose decisions with the live model"), disabled=not llm_available()):
                        try:
                            with st.spinner(t("Reading your report with the model… this can take a minute.")):
                                orc.extract_project_decisions(actor=cx.viewer or "agent")
                            st.rerun()
                        except (LLMUnavailable, ValueError) as err:
                            st.error(str(err))
                    if not llm_available():
                        st.caption(orc.EXTRACTION_NEEDS_MODEL)
                with st.form("add-decision", clear_on_submit=True):
                    st.caption(t("Copy the quote word for word from the document; it is checked against that page."))
                    d_title = st.text_input(t("Decision (what the team chose)"))
                    d_why = st.text_area(t("Rationale (why, in the team's words)"), height=70)
                    d_alts = st.text_input(t("Rejected alternatives (comma-separated)"))
                    d_file = st.selectbox(t("Document"), p.source_files)
                    d_page = st.number_input(t("Page"), min_value=1, step=1)
                    d_quote = st.text_area(t("Exact quote from that page"), height=70)
                    if st.form_submit_button(t("Add decision")):
                        try:
                            card = orc.add_decision(title=d_title, rationale=d_why, alternatives=d_alts.split(","),
                                                    source_file=d_file, page=int(d_page), quote=d_quote,
                                                    actor=cx.viewer or "agent")
                            if card.review_status == ReviewStatus.unsupported:
                                st.warning(t("Added, but the quote was not found on that page, so it can never be "
                                             "assessed. Check the page number and the exact wording."))
                            else:
                                st.rerun()
                        except ValueError as err:
                            st.error(str(err))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("Decisions"), len(cx.cards))
    c2.metric(t("Confirmed"), len(by_status[ReviewStatus.verified]))
    c3.metric(t("Needs review"), len(by_status[ReviewStatus.proposed]))
    c4.metric(t("No source"), len(by_status[ReviewStatus.unsupported]))

    if not cx.cards:
        empty_state("doc", "No decisions yet",
                    "Add the project's key decisions below: each quote is checked against your document.")
    for d in cx.cards.values():
        with st.container(border=True):
            label, kind = CARD_PILL[d.review_status.value]
            left, right = st.columns([5, 1.4])
            left.markdown(f"**{dlabel(d.id)} · {d.title}**")
            with right:
                show(pill(label, kind))
            st.write(d.rationale)
            info = []
            if d.alternatives:
                info.append(f"Rejected: {esc(', '.join(d.alternatives))}")
            info.append(f"Owner: {esc(cx.names.get(d.owner_id, 'not declared'))}")
            show(f'<div class="bf-muted">{" · ".join(info)}</div>')
            for r in d.source_refs:
                show(quote_block(r))
            if d.review_status == ReviewStatus.unsupported:
                st.warning(t("No verified source: the quote is not on the cited page, so this decision is never assessed."))
            if d.review_status == ReviewStatus.proposed:
                show('<div class="bf-muted">' + esc(t("Proposed: not assessed until a member checks the quote and confirms it.")) + '</div>')
                if cx.viewer is None:
                    show('<div class="bf-muted">' + (t("Enter your access code in the sidebar to continue.") if cx.locked
                         else t("Add members first: only a member can confirm a decision.")) + '</div>')
                else:
                    owner = st.selectbox(t("Owner (who made this decision)"), [None, *cx.members], key=f"owner-{d.id}",
                                         format_func=lambda m: t("not declared") if m is None else cx.names[m])
                    if st.button(t("Confirm card"), key=f"confirm-{d.id}"):
                        orc.confirm_decision(d.id, {"owner_id": owner} if owner else None, actor=cx.viewer)
                        st.rerun()

    if not demo:
        with st.expander(t("Delete this project")):
            st.caption(t("Deletes this project's decisions, members, answers, missions and log. It cannot be undone. "
                         "Other projects and the demo are not affected."))
            typed = st.text_input(t("Type the project title to confirm"), key="delete-title")
            if st.button(t("Delete project"), disabled=typed.strip() != p.title):
                orc.delete_project(p.id, typed, actor=cx.viewer or "agent")
                st.rerun()

    page_nav(1)
