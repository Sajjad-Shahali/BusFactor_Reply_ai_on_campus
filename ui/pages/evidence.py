"""Page 6: sources, action log, abstentions, review queue and limits."""
from __future__ import annotations


import pandas as pd
import streamlit as st

from busfactor import orchestrator as orc
from busfactor.i18n import t
from ui.state import ctx
from ui.widgets import (
    dlabel, empty_state, esc, humanize_action, need_viewer, next_step_card, page_header, page_nav, pill, privacy_panel, show,
)


def render() -> None:
    cx = ctx()
    page_header(6, "Evidence & Limits", "Where every decision comes from, what the agent did, and what it can't do.")
    need_viewer()
    next_step_card()
    privacy_panel()
    log = orc.team_log(cx.viewer)  # team events + the viewer's own private steps, never other members'

    show_details = st.toggle(t("Show technical details"), key="log-details")

    def log_table(events):
        """Plain sentences by default; the raw action names and details only when asked for."""
        rows = []
        for e in events:
            row = {t("Time"): e.ts.strftime("%Y-%m-%d %H:%M"), t("Who"): e.actor,
                   t("What happened"): humanize_action(e.action)}
            if show_details:
                row[t("Action")] = e.action
                row[t("Detail")] = str(e.detail)
            rows.append(row)
        return pd.DataFrame(rows)

    sources, actions, abstain, review, limits = st.tabs(
        [t("Sources"), t("Action log"), t("Abstentions & blocked"), t("Review queue"), t("Limits")])
    with sources:
        st.dataframe(pd.DataFrame([{
            "Decision": dlabel(d.id), "Status": d.review_status.value,
            "File": ", ".join(r.file for r in d.source_refs) or "none",
            "Page": ", ".join(str(r.page) for r in d.source_refs),
            "Quote": " / ".join(r.quote for r in d.source_refs),
        } for d in cx.cards.values()]), hide_index=True, width="stretch")
    with actions:
        st.caption("Shared project steps, plus your own private steps. Other members' checks, consents and "
                   "retests are never shown here, and answers and scores are never written to the log.")
        st.dataframe(log_table(log[::-1]), hide_index=True, width="stretch")
    with abstain:
        flagged = [e for e in log if any(k in e.action for k in ("abstain", "blocked", "answer_request"))
                   or e.detail.get("abstained")]
        if flagged:
            st.dataframe(log_table(flagged), hide_index=True, width="stretch")
        else:
            st.write(t("None yet."))
    with review:
        st.caption(t("Answers the model could not score wait here for a human. A reviewer sees only answers from "
                     "members who agreed to human review, and never their names."))
        reviewer_code = (st.text_input(t("Reviewer code"), type="password", key="reviewer-code")
                         if orc.is_protected() else None)
        try:
            queue = orc.review_queue(reviewer_code=reviewer_code)
        except PermissionError:
            queue = None
            st.info(t("Enter the reviewer code to open the queue."))
        if queue is not None and not queue:
            empty_state("shield", "Nothing is waiting for review",
                        "When a member who agreed to human review has an answer the model could not score, it appears here.")
        for item in queue or []:
            with st.container(border=True):
                show(f'{pill(item.question_type.replace("_", " ").title(), "blue")} '
                     f'<span class="bf-muted">{esc(dlabel(item.decision_id))} · {esc(item.decision_title)}</span>')
                show(f'<div class="bf-question">{esc(item.prompt)}</div>')
                show(f'<div class="bf-muted">{esc(t("Answer"))}: {esc(item.answer)}</div>')
                for quote in item.source_quotes:
                    show(f'<div class="bf-quote">“{esc(quote)}”</div>')
                if item.rubric_expectations:
                    st.markdown(t("A good answer covers:") + "\n" + "\n".join(f"- {x}" for x in item.rubric_expectations))
                with st.form(f"review-{item.evidence_id}"):
                    score = st.radio(t("Score"), [0, 1, 2], horizontal=True, key=f"rv-score-{item.evidence_id}")
                    note = st.text_input(t("Feedback for the member (optional)"), key=f"rv-note-{item.evidence_id}")
                    if st.form_submit_button(t("Save review"), type="primary"):
                        orc.apply_review(item.evidence_id, score, note, reviewer_code=reviewer_code)
                        st.rerun()
    with limits:
        st.markdown(
            "- Scores are practice feedback, not grades. A score from the model can be wrong.\n"
            "- One correct answer shows someone explained one decision on one day, not that they'll remember it.\n"
            "- Decision Coverage is a prototype indicator, not a validated metric.\n"
            "- In the synthetic demo, answers are scored offline with a keyword rubric on made-up data, as a stand-in "
            "for the model. A score of 2 also needs explained reasoning and the scenario's own conclusion.\n"
            "- In your own projects without the live model, nothing is scored automatically: answers wait for human "
            "review. With the model, unsure or inconsistent grades also go to human review.\n"
            "- Answers that try to instruct the grader are never scored. The app cannot stop anyone from using an "
            "outside AI tool.\n"
            "- No source means no assessment. A decision is assessed only after a member confirms it.\n"
            "- If nobody can explain a decision, the app points to the course material or the TA.\n"
            "- In a small team even totals can identify people, so the team view shows only counts per decision."
        )

    page_nav(6)
