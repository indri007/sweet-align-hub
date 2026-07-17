"""
JobMatch AI — Main Streamlit Application
AI-powered CV Review & Job Recommendation App

Wizard-style UI with 5 sequential steps:
A. Input CV → B. Lowongan Kerja → C. Review CV → D. Konsultasi Karir → E. Mock Interview

Modularized (Tahap 3 — Struktur Kode): this file now only handles
auth, page config, session init, sidebar, and dispatch to the
pages/step_*.py modules. Each step's own UI logic lives in its
own module under pages/. No behavior was changed during this split —
every block below is functionally identical to the original
monolithic app.py.
"""

import streamlit as st
import auth_setup
auth_setup.require_google_login()
auth_setup.show_user_badge_and_logout(location="sidebar")
from pathlib import Path

import config
from customer_service_chat_floating import render_cs_chatbot
from database import DatabaseManager
from vector_store import VectorStoreManager

import nav
from nav import STEPS, go_to_step
from pages.step_a_input_cv import render_step_a
from pages.step_b_jobs import render_step_b
from pages.step_c_review import render_step_c
from pages.step_d_consultation import render_step_d
from pages.step_e_interview import render_step_e

import os
import sentry_sdk
from health_server import start_health_server

# ─── Observability: Sentry + health check server ──────────
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.getenv("ENVIRONMENT", "development"),
        traces_sample_rate=0.1,
    )

if "_health_server_started" not in st.session_state:
    start_health_server()
    st.session_state["_health_server_started"] = True


# ─── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="JobMatch AI — CV Review & Job Recommendations",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Google Auth Check ─────────────────────────────────────
# NOTE: kept exactly as in the original app.py. This duplicates
# auth_setup.require_google_login() above; flagged as a Tahap 6
# (File Cleanup) candidate rather than changed here, to keep this
# modularization behavior-neutral.
if not st.user.is_logged_in:
    st.title("🎯 JobMatch AI")
    st.write("Silakan login dengan akun Google untuk melanjutkan.")
    if st.button("Login dengan Google"):
        st.login()
    st.stop()

st.sidebar.write(f"👋 Halo, {st.user.name}")
st.sidebar.write(f"📧 {st.user.email}")
if st.sidebar.button("Logout"):
    st.logout()

# ─── Load CSS ─────────────────────────────────────────────
css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ─── Session State Initialization ─────────────────────────
nav.init_session_state()

# ─── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🎯 JobMatch AI")
    st.markdown("---")

    # Step navigation
    for i, step in enumerate(STEPS):
        is_active = i == st.session_state.current_step
        is_completed = (i == 0 and st.session_state.cv_uploaded) or (
            i < st.session_state.current_step and st.session_state.cv_uploaded
        )
        is_locked = i > 0 and not st.session_state.cv_uploaded

        # Determine visual state
        if is_active:
            icon_class = "active"
            item_class = "active"
            label_class = ""
        elif is_completed:
            icon_class = "completed"
            item_class = "completed"
            label_class = ""
        elif is_locked:
            icon_class = "locked"
            item_class = "locked"
            label_class = "locked"
        else:
            icon_class = "locked"
            item_class = ""
            label_class = ""

        # Render step item
        icon_content = "✓" if is_completed and not is_active else step["key"]

        st.markdown(
            f"""<div class="step-item {item_class}">
                <div class="step-icon {icon_class}">{icon_content}</div>
                <div class="step-label {label_class}">{step['emoji']} {step['label']}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Make clickable via button (hidden in a column trick)
        if not is_locked:
            if st.button(
                f"Go to {step['label']}",
                key=f"nav_{i}",
                use_container_width=True,
                type="secondary" if not is_active else "primary",
            ):
                go_to_step(i)
                st.rerun()

    # Progress bar
    st.markdown("---")
    progress = (st.session_state.current_step + 1) / len(STEPS)
    progress_pct = int(progress * 100)
    st.markdown(
        f"""<div style="text-align:center; margin-bottom:8px;">
            <span style="color:var(--text-secondary); font-size:0.82rem;">
                📊 Progress: Step {st.session_state.current_step + 1}/{len(STEPS)}
            </span>
        </div>
        <div class="progress-container">
            <div class="progress-fill" style="width:{progress_pct}%"></div>
        </div>""",
        unsafe_allow_html=True,
    )

    # API Status
    st.markdown("---")
    if config.is_gemini_configured():
        st.success("✅ Gemini AI Connected", icon="🔑")
    else:
        st.warning("⚠️ Gemini API key belum diatur", icon="🔑")
        st.caption("Tambahkan di file `.env`")

# ─── Step Dispatch ─────────────────────────────────────────
if st.session_state.current_step == 0:
    render_step_a()
elif st.session_state.current_step == 1:
    render_step_b()
elif st.session_state.current_step == 2:
    render_step_c()
elif st.session_state.current_step == 3:
    render_step_d()
elif st.session_state.current_step == 4:
    render_step_e()

render_cs_chatbot()
