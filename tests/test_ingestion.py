"""Teammate 1 tests: ingestion + decision cards (brief test 1). Run: PYTHONPATH=src pytest tests/test_ingestion.py"""
import json
from pathlib import Path

import pytest

from busfactor.ingestion import load_pages
from busfactor.knowledge import confirm_card, extract_decisions, load_demo_decisions, quote_on_page
from busfactor.models import ReviewStatus

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "demo" / "project_report.md"
DECISIONS = ROOT / "data" / "demo" / "decisions.json"


@pytest.fixture(autouse=True)
def no_demo_mode(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)


def fake_llm(items):
    return lambda prompt, schema: {"decisions": items}


# --- ingestion

def test_demo_report_has_four_numbered_pages():
    assert [n for n, _ in load_pages(REPORT)] == [1, 2, 3, 4]


def test_empty_file_gives_no_pages_and_no_cards(tmp_path):
    empty = tmp_path / "empty.md"
    empty.write_text("")
    assert load_pages(empty) == []
    assert extract_decisions([str(empty)], llm=fake_llm([])) == []


def test_unsupported_file_type_is_rejected(tmp_path):
    f = tmp_path / "x.docx"
    f.write_text("x")
    with pytest.raises(ValueError):
        load_pages(f)


# --- test 1: every demo card cites a real file/page

def test_every_demo_quote_is_on_its_cited_page():
    raw = json.loads(DECISIONS.read_text())
    assert raw["_note"].startswith("SYNTHETIC DEMO DATA")
    pages = load_pages(REPORT)
    for d in raw["decisions"]:
        assert d["source_refs"], d["id"]
        for ref in d["source_refs"]:
            assert quote_on_page(ref["quote"], pages, ref["page"]), d["id"]


def test_demo_mode_returns_five_verified_cards(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    cards = extract_decisions(["ignored.pdf"])
    assert [c.id for c in cards] == ["D01", "D02", "D03", "D04", "D05"]
    assert all(c.review_status == ReviewStatus.verified for c in cards)
    assert cards == load_demo_decisions()


# --- extraction: quotes are checked in code

GOOD = {"title": "F1 as headline metric", "rationale": "Class imbalance", "page": 2,
        "quote": "We report F1 instead of accuracy as our headline metric because of the class imbalance."}


def test_real_quote_becomes_proposed_card_with_source():
    [card] = extract_decisions([str(REPORT)], llm=fake_llm([GOOD]))
    assert card.review_status == ReviewStatus.proposed  # not verified until a human confirms
    assert card.source_refs[0].page == 2 and card.owner_id is None


def test_invented_quote_becomes_unsupported():
    bad = GOOD | {"quote": "We chose F1 because the professor told us to."}
    [card] = extract_decisions([str(REPORT)], llm=fake_llm([bad]))
    assert card.review_status == ReviewStatus.unsupported and card.source_refs == []


def test_real_quote_on_wrong_page_becomes_unsupported():
    [card] = extract_decisions([str(REPORT)], llm=fake_llm([GOOD | {"page": 3}]))
    assert card.review_status == ReviewStatus.unsupported


def test_quote_matching_ignores_line_breaks_and_case():
    pages = [(1, "We report F1\ninstead of   ACCURACY.")]
    assert quote_on_page("we report f1 instead of accuracy.", pages, 1)
    assert not quote_on_page("", pages, 1)


def test_at_most_five_cards_with_sequential_ids():
    cards = extract_decisions([str(REPORT)], llm=fake_llm([GOOD] * 8))
    assert [c.id for c in cards] == ["D01", "D02", "D03", "D04", "D05"]


# --- human review

def test_confirm_card_applies_edits_and_verifies():
    [card] = extract_decisions([str(REPORT)], llm=fake_llm([GOOD]))
    confirmed = confirm_card(card, {"owner_id": "M02", "title": "Use F1 instead of accuracy"})
    assert confirmed.review_status == ReviewStatus.verified
    assert confirmed.owner_id == "M02" and confirmed.title == "Use F1 instead of accuracy"


def test_confirm_card_refuses_unsupported_card_and_source_edits():
    [bad] = extract_decisions([str(REPORT)], llm=fake_llm([GOOD | {"page": 3}]))
    with pytest.raises(ValueError):
        confirm_card(bad)
    [good] = extract_decisions([str(REPORT)], llm=fake_llm([GOOD]))
    with pytest.raises(ValueError):
        confirm_card(good, {"source_refs": []})


def _two_column_pdf(path):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, 790, "A Title That Runs Across Both Columns Of The Page")
    c.setFont("Helvetica", 10)
    left = ["We chose PostgreSQL because seats must", "never be sold twice, and a transaction", "guarantees that for us."]
    right = ["The index on event and start time cut", "the timetable query from two seconds", "to a few milliseconds."]
    for i, (a, b) in enumerate(zip(left, right, strict=True)):
        c.drawString(60, 740 - 14 * i, a)
        c.drawString(320, 740 - 14 * i, b)
    for i in range(3, 8):   # more two-column lines, so the page is clearly a two-column one
        c.drawString(60, 740 - 14 * i, f"left filler line number {i}")
        c.drawString(320, 740 - 14 * i, f"right filler line number {i}")
    c.save()


def test_a_two_column_pdf_is_read_one_column_at_a_time(tmp_path):
    from busfactor import ingestion

    pdf = tmp_path / "paper.pdf"
    _two_column_pdf(pdf)
    text = ingestion.load_pages(pdf)[0][1]
    assert "A Title That Runs Across Both Columns Of The Page" in text
    # a sentence that wraps over several lines of ONE column stays together
    assert "never be sold twice, and a transaction guarantees" in " ".join(text.split())
    assert "cut the timetable query from two seconds to a few" in " ".join(text.split())


def test_a_quote_survives_a_hyphenated_line_break():
    from busfactor.knowledge import quote_on_page

    pages = [(1, "Bridging the sim-to-real gap in reinforcement learn-\ning requires policies that stay reliable.")]
    assert quote_on_page("reinforcement learning requires policies that stay reliable", pages, 1)
    assert not quote_on_page("reinforcement learning requires policies that never fail", pages, 1)
    assert not quote_on_page("learning", pages, 1)          # too short to count as a match after squashing
