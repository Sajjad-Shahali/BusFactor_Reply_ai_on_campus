"""Per-session UI state.

app.py builds a fresh Ctx on every run and stores it in st.session_state, so one browser session can never see
another session's identity (a module-level global would be shared by every session of the server process).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import streamlit as st


@dataclass
class Ctx:
    members: dict = field(default_factory=dict)      # members of the open project
    names: dict = field(default_factory=dict)        # member id -> display name
    cards: dict = field(default_factory=dict)        # decision id -> DecisionCard
    labels: dict = field(default_factory=dict)       # people and decisions, for explain_mission
    viewer: Optional[str] = None                     # the signed-in / selected member (None: nobody or locked)
    locked: bool = False                             # a protected project is waiting for the member's access code
    protected: bool = False                          # the open project uses access codes
    unlocked: set = field(default_factory=set)       # members unlocked in this browser session


def ctx() -> Ctx:
    context: Any = st.session_state["_ctx"]
    return context
