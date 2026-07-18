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
import os
import sentry_sdk
import streamlit as st

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN", ""),
    traces_sample_rate=0.2,       # 20% transaksi buat performance tracing
    environment=os.environ.get("ENVIRONMENT", "production"),
)

# ─── Page Config ──────────────────────────────────────────
# Set page config at the very top. Dynamically collapse sidebar if not logged in
# to prevent the native sidebar from flashing before CSS injection takes effect.
is_logged_in = getattr(st.user, "is_logged_in", False)
st.set_page_config(
    page_title="JobMatch AI — CV Review & Job Recommendations",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded" if is_logged_in else "collapsed",
)

from logger import get_logger
import health_check

logger = get_logger(__name__)


@st.cache_data(ttl=60)
def get_system_health():
    """Runs all deep health checks and caches the result for 60 seconds."""
    return health_check.run_all_checks()


import config
import auth_setup
auth_setup.require_google_login()
auth_setup.show_user_badge_and_logout(location="sidebar")
from pathlib import Path

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

# (Page config has been moved to the top of the file)

# ─── Google Auth Check ─────────────────────────────────────
# NOTE: kept exactly as in the original app.py. This duplicates
# auth_setup.require_google_login() above; flagged as a Tahap 6
# (File Cleanup) candidate rather than changed here, to keep this
# modularization behavior-neutral.
if not st.user.is_logged_in:
    st.title("🎯 JobMatch AI")
    st.write("Silakan login dengan akun Google untuk melanjutkan.")
    if st.button("Login dengan Google"):
        st.login("google")
    st.stop()

st.sidebar.write(f"👋 Halo, {st.user.name}")
st.sidebar.write(f"📧 {st.user.email}")
if st.sidebar.button("Logout"):
    st.logout()

# ─── Load CSS ─────────────────────────────────────────────
from theme import inject_material3_theme
inject_material3_theme()

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

    # API & Database System Status
    st.markdown("---")
    st.markdown("#### 📊 System Status")

    try:
        health_results = get_system_health()
        checks = health_results.get("checks", {})

        # Gemini API Status
        gemini_status = checks.get("gemini", {}).get("status", "unreachable")
        gemini_latency = checks.get("gemini", {}).get("latency_ms", 0)
        if gemini_status == "ok":
            st.success(f"Gemini API: OK ({gemini_latency}ms)", icon="🔑")
        else:
            st.error("Gemini API: Error", icon="🔑")

        # Qdrant Database Status
        qdrant_status = checks.get("qdrant", {}).get("status", "unreachable")
        qdrant_latency = checks.get("qdrant", {}).get("latency_ms", 0)
        if qdrant_status == "ok":
            st.success(f"Qdrant DB: OK ({qdrant_latency}ms)", icon="🎯")
        else:
            st.error("Qdrant DB: Error", icon="🎯")

        # Aiven MySQL Database Status
        db_status = checks.get("database", {}).get("status", "unreachable")
        db_latency = checks.get("database", {}).get("latency_ms", 0)
        if db_status == "ok":
            st.success(f"MySQL DB: OK ({db_latency}ms)", icon="💾")
        else:
            st.error("MySQL DB: Error", icon="💾")
    except Exception as e:
        st.error(f"Failed to check health: {str(e)}")

    # N8N Status
    if config.USE_N8N:
        if config.is_n8n_configured():
            st.success("N8N: Active", icon="🔗")
        else:
            st.warning("N8N: Not Configured", icon="🔗")
    else:
        st.info("Mode: Local (No N8N)", icon="🏠")

    # Refresh button
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


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
