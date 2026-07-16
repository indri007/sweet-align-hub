"""
auth_setup.py — Login dengan Google Account untuk Streamlit (Cloud Run friendly)
"""

import os
import streamlit as st
from streamlit.runtime.secrets import secrets_singleton

_GOOGLE_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"


def _inject_auth_secrets():
    redirect_uri = os.environ.get("AUTH_REDIRECT_URI", "")
    cookie_secret = os.environ.get("AUTH_COOKIE_SECRET", "")
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    missing = [
        name
        for name, val in [
            ("AUTH_REDIRECT_URI", redirect_uri),
            ("AUTH_COOKIE_SECRET", cookie_secret),
            ("GOOGLE_CLIENT_ID", client_id),
            ("GOOGLE_CLIENT_SECRET", client_secret),
        ]
        if not val
    ]
    if missing:
        return False, missing

    secrets_singleton._secrets = {
        "auth": {
            "redirect_uri": redirect_uri,
            "cookie_secret": cookie_secret,
            "client_id": client_id,
            "client_secret": client_secret,
            "server_metadata_url": _GOOGLE_METADATA_URL,
        }
    }
    return True, []


def require_google_login():
    ok, missing = _inject_auth_secrets()

    if not ok:
        st.error(
            "⚠️ Konfigurasi Google Login belum lengkap. "
            f"Environment variable berikut belum diisi: {', '.join(missing)}"
        )
        st.stop()

    if not st.user.is_logged_in:
        st.markdown('<style>section.stMain, div.stApp { }</style><div class="jm-hide-sidebar"></div>', unsafe_allow_html=True)
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] { display: none !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        with st.container():
            st.markdown('<div class="jm-login-btn-marker"></div>', unsafe_allow_html=True)
            st.markdown('<div class="jm-top-login-bar"></div>', unsafe_allow_html=True)
            _c1, _c2 = st.columns([3, 1])
            with _c2:
                if st.button("Masuk dengan Google", use_container_width=True, type="primary", icon=":material/login:"):
                    st.login()

        st.markdown(
            """
            <div class="jm-landing">
                <div class="jm-landing-grid">
                    <div>
                        <div class="jm-landing-brand">
                            <div class="jm-landing-brand-icon">💼</div>
                            <span class="jm-landing-brand-text">JobMatch AI</span>
                        </div>
                        <h1>Lowongan impianmu,<br>tinggal selangkah<br>dari CV-mu.</h1>
                        <p class="jm-landing-sub">
                            Upload CV kamu dan biarkan AI membantu mencari lowongan
                            yang cocok, meninjau CV, dan berlatih interview -
                            semua dalam satu aplikasi.
                        </p>
                        <div class="jm-landing-stats">
                            <div>
                                <p class="jm-landing-stat-num">500+</p>
                                <p class="jm-landing-stat-label">Lowongan kerja Indonesia</p>
                            </div>
                            <div>
                                <p class="jm-landing-stat-num">5</p>
                                <p class="jm-landing-stat-label">Fitur berbasis AI</p>
                            </div>
                        </div>
                        <div class="jm-photo-card">
                            <img src="data:image/jpeg;base64,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" alt="Tim support JobMatch AI" />
                        </div>
                    </div>
                    <div class="jm-landing-features">
                        <p class="jm-landing-right-title">Dapat kerja dengan AI dan data lowongan asli.</p>
                        <div class="jm-feature-card">
                            <div class="jm-feature-icon">📄</div>
                            <div>
                                <p class="jm-feature-title">Review CV & Skor ATS</p>
                                <p class="jm-feature-desc">Feedback langsung, generate & download CV ATS-friendly dalam Bahasa Indonesia atau Inggris, menyesuaikan bahasa CV asli kamu.</p>
                            </div>
                        </div>
                        <div class="jm-feature-card">
                            <div class="jm-feature-icon">🎯</div>
                            <div>
                                <p class="jm-feature-title">Rekomendasi Lowongan</p>
                                <p class="jm-feature-desc">Pencocokan semantik dari ratusan lowongan kerja Indonesia.</p>
                            </div>
                        </div>
                        <div class="jm-feature-card">
                            <div class="jm-feature-icon">🎤</div>
                            <div>
                                <p class="jm-feature-title">Mock Interview AI</p>
                                <p class="jm-feature-desc">Simulasi wawancara kerja, mode text maupun voice.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="jm-landing-trust">
                <p class="jm-landing-trust-text">
                    Dibangun khusus untuk pencari kerja Indonesia - didukung Gemini AI
                    dan database lowongan kerja nyata, bukan data simulasi.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="jm-landing-stripe">
                <div class="jm-landing-stripe-stat">
                    <div class="jm-landing-stripe-num">500+</div>
                    <div class="jm-landing-stripe-label">Lowongan kerja aktif</div>
                </div>
                <div class="jm-landing-stripe-stat">
                    <div class="jm-landing-stripe-num">5</div>
                    <div class="jm-landing-stripe-label">Fitur berbasis AI dalam 1 aplikasi</div>
                </div>
                <div class="jm-landing-stripe-stat">
                    <div class="jm-landing-stripe-num">100%</div>
                    <div class="jm-landing-stripe-label">Login aman Google OAuth</div>
                </div>
            </div>
            <div class="jm-landing-footer">
                <span>Tentang Kami</span>
                <span>Fitur</span>
                <span>Cara Kerja</span>
                <span>Bantuan</span>
                <span>Kebijakan Privasi</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()


def show_user_badge_and_logout(location="sidebar"):
    target = st.sidebar if location == "sidebar" else st
    with target:
        name = getattr(st.user, "name", None) or getattr(st.user, "email", "User")
        picture = getattr(st.user, "picture", None)
        if picture:
            target.markdown(
                f"""
                <div class="gauth-avatar-wrap">
                    <img class="gauth-avatar-img" src="{picture}" />
                    <span class="gauth-avatar-name">👋 {name}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            target.markdown(f"**👋 {name}**")
        if target.button("Logout", key="btn_logout_google"):
            st.logout()
