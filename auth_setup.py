"""
auth_setup.py — Login dengan Google Account untuk Streamlit

Mendukung dua mode:
- Streamlit Cloud  → redirect ke https://jobsmatch.streamlit.app/_auth/callback
- Cloud Run / lokal → pakai AUTH_REDIRECT_URI dari env

OAuth Client terdaftar (17 Jul 2026):
  Client ID : 443770912596-sartmrtk9aeadbdvrqqdsf4o2bgiddtn.apps.googleusercontent.com
  Redirect URIs yang didaftarkan di Google Console:
    - https://jobsmatch.streamlit.app/_auth/callback   ← Streamlit native auth
    - https://jobsmatch.streamlit.app/oauth2callback
    - http://localhost:8501/oauth2callback
    - https://digimetashop.web.id
"""

import os
import streamlit as st
from streamlit.runtime.secrets import secrets_singleton

_GOOGLE_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Redirect URI default untuk Streamlit Cloud
_DEFAULT_REDIRECT_URI = "https://jobsmatch.streamlit.app/_auth/callback"


def _inject_auth_secrets():
    # Prioritas: env var → default Streamlit Cloud URL
    redirect_uri = (
        os.environ.get("AUTH_REDIRECT_URI")
        or _get_streamlit_secret("auth", "redirect_uri")
        or _DEFAULT_REDIRECT_URI
    )
    cookie_secret = os.environ.get("AUTH_COOKIE_SECRET", "")
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    # Fallback ke Streamlit secrets (untuk Streamlit Cloud deployment)
    if not client_id:
        client_id = _get_streamlit_secret("auth", "client_id") or ""
    if not client_secret:
        client_secret = _get_streamlit_secret("auth", "client_secret") or ""
    if not cookie_secret:
        cookie_secret = _get_streamlit_secret("auth", "cookie_secret") or ""

    missing = [
        name
        for name, val in [
            ("GOOGLE_CLIENT_ID", client_id),
            ("GOOGLE_CLIENT_SECRET", client_secret),
            ("AUTH_COOKIE_SECRET", cookie_secret),
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


def _get_streamlit_secret(section: str, key: str) -> str:
    """Ambil nilai dari st.secrets tanpa crash kalau tidak ada."""
    try:
        return st.secrets.get(section, {}).get(key, "")
    except Exception:
        return ""


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
