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
        st.markdown(
            """
            <div style="text-align:center; padding-top: 8vh;">
                <h2>🔐 Selamat Datang</h2>
                <p>Silakan login dengan akun Google untuk melanjutkan.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔑 Login dengan Google", use_container_width=True, type="primary"):
                st.login()
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
