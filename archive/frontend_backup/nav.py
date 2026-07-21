"""
Wizard navigation — step definitions and navigation helpers.

Extracted from app.py during modularization (Tahap 3 — Struktur Kode).
Lives in its own module (rather than app.py) so that both app.py and
the individual pages/*.py modules can import it without a circular
import.
"""

import streamlit as st

STEPS = [
    {"key": "A", "label": "Input CV", "icon": "📄", "emoji": "📄"},
    {"key": "B", "label": "Lowongan Kerja", "icon": "💼", "emoji": "💼"},
    {"key": "C", "label": "Review CV", "icon": "✍️", "emoji": "✍️"},
    {"key": "D", "label": "Konsultasi Karir", "icon": "💬", "emoji": "💬"},
    {"key": "E", "label": "Mock Interview", "icon": "🎤", "emoji": "🎤"},
]

SESSION_DEFAULTS = {
    "current_step": 0,
    "cv_uploaded": False,
    "cv_text": "",
    "cv_filename": "",
    "cv_file_info": {},
    "cv_bytes": None,
    "job_matches": [],
    "ai_summary": None,
    "cv_feedback": None,
    "ats_cv_text": None,
    "career_chat_history": [],
    "interview_history": [],
    "interview_job": None,
    "interview_started": False,
}


def init_session_state():
    """Populate st.session_state with defaults for any missing keys."""
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to_step(step_idx: int):
    """Navigate to a specific step."""
    if step_idx == 0 or st.session_state.cv_uploaded:
        st.session_state.current_step = step_idx


def next_step():
    """Go to the next step."""
    if st.session_state.current_step < len(STEPS) - 1:
        go_to_step(st.session_state.current_step + 1)


def prev_step():
    """Go to the previous step."""
    if st.session_state.current_step > 0:
        go_to_step(st.session_state.current_step - 1)
