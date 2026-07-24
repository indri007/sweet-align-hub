"""
auth_setup.py — Login dengan Google Account untuk Streamlit (Cloud Run friendly)
"""

import os
import streamlit as st
from streamlit.runtime.secrets import secrets_singleton

_GOOGLE_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"


def _get_secret(key: str) -> str:
    """Baca dari st.secrets dulu (Streamlit Cloud), fallback ke os.environ (lokal)."""
    try:
        if key in st.secrets:
            val = st.secrets[key]
            if val:
                return str(val)
    except Exception:
        pass
    return os.environ.get(key, "")


def _inject_auth_secrets():
    redirect_uri = _get_secret("AUTH_REDIRECT_URI")
    cookie_secret = _get_secret("AUTH_COOKIE_SECRET")
    client_id = _get_secret("GOOGLE_CLIENT_ID")
    client_secret = _get_secret("GOOGLE_CLIENT_SECRET")
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
            "google": {
                "client_id": client_id,
                "client_secret": client_secret,
                "server_metadata_url": _GOOGLE_METADATA_URL,
            }
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
        # Load styles.css on the landing page as well
        styles_content = ""
        from pathlib import Path
        css_path = Path(__file__).parent / "styles.css"
        if css_path.exists():
            styles_content = css_path.read_text(encoding="utf-8")

        # Hide sidebar on landing page
        st.markdown(
            f"""
            <style>
            [data-testid="stSidebar"] {{ display: none !important; }}
            #MainMenu {{ visibility: hidden; }}
            footer {{ visibility: hidden; }}
            header {{ visibility: hidden; }}
            .stApp {{ background: var(--m3-bg-base) !important; }}
            {styles_content}
            </style>
            """,
            unsafe_allow_html=True,
        )

        # ─── Top Navigation Bar ───
        _nav1, _nav2 = st.columns([5, 1])
        with _nav1:
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:10px;padding:12px 0 8px 0;font-family:'Inter',sans-serif;">
                    <div style="display:grid;height:36px;width:36px;place-items:center;border-radius:10px;background:var(--m3-primary);box-shadow:0 2px 8px rgba(66,133,244,0.3);">
                        <span style="color:white;font-size:1.1rem;font-weight:900;">⚡</span>
                    </div>
                    <span style="font-size:1.25rem;font-weight:800;color:var(--m3-on-bg);letter-spacing:-0.02em;">JobMatch<span style="color:var(--m3-primary);">AI</span></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with _nav2:
            st.write("")
            if st.button("Masuk Google", type="primary", use_container_width=True, key="nav_login_btn"):
                st.login("google")

        st.divider()

        # ─── Hero Section ───
        _hero1, _hero2 = st.columns([1.1, 0.9], gap="large")
        with _hero1:
            st.markdown(
                """
                <div style="padding:20px 0 32px 0;font-family:'Inter',sans-serif;">
                    <div style="display:inline-flex;align-items:center;gap:8px;border-radius:100px;background:rgba(66,133,244,0.15);border:1px solid rgba(66,133,244,0.3);padding:7px 16px;margin-bottom:22px;">
                        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#4285F4;animation:pulse 2s infinite;"></span>
                        <span style="font-size:0.72rem;font-weight:700;color:#93c5fd;text-transform:uppercase;letter-spacing:0.06em;">AI-Powered · Made in Indonesia 🇮🇩</span>
                    </div>
                    <h1 style="font-size:3.2rem;line-height:1.1;font-weight:800;color:var(--m3-on-bg);margin:0 0 20px 0;letter-spacing:-0.03em;">
                        Your CV Ditolak Robot Sebelum Sampai ke <span style="color:var(--m3-primary);">HRD.</span>
                    </h1>
                    <p style="font-size:1.1rem;line-height:1.65;color:var(--m3-on-surface-variant);margin:0 0 28px 0;max-width:520px;">
                        JobMatch AI scan CV kamu persis kayak sistem ATS yang dipakai perusahaan — instant scoring, actionable insights, plus AI mock interview. Try it, gratis.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Render buttons side-by-side using columns
            _btn_col1, _btn_col2 = st.columns([1, 1.2])
            with _btn_col1:
                if st.button("Get My CV Score  →", type="primary", use_container_width=True, key="hero_cta_btn"):
                    st.login("google")
            with _btn_col2:
                if st.button("Sign in with Google", type="secondary", use_container_width=True, key="hero_google_btn", icon=":material/login:"):
                    st.login("google")

            st.markdown(
                """
                <div style="display:flex;flex-wrap:wrap;gap:20px;margin-top:24px;font-family:'Inter',sans-serif;">
                    <span style="display:inline-flex;align-items:center;gap:6px;font-size:0.88rem;font-weight:600;color:var(--m3-success);">✓ No credit card</span>
                    <span style="display:inline-flex;align-items:center;gap:6px;font-size:0.88rem;font-weight:600;color:var(--m3-success);">✓ Results in 2 minutes</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with _hero2:
            st.markdown(
                """
                <div style="padding:20px 0 0 0;font-family:'Inter',sans-serif;perspective:1000px;">
                    <div style="background:linear-gradient(135deg,#1a73e8,#4285F4 50%,#1557b0);border-radius:28px;padding:20px;box-shadow:0 30px 60px rgba(66,133,244,0.35);transform:rotateY(-15deg) rotateX(10deg);transform-style:preserve-3d;transition:transform 0.5s ease;" onmouseover="this.style.transform='rotateY(-5deg) rotateX(5deg) translateY(-5px)'" onmouseout="this.style.transform='rotateY(-15deg) rotateX(10deg)'">
                        <div style="background:white;border-radius:18px;overflow:hidden;box-shadow:0 15px 30px rgba(0,0,0,0.1);transform:translateZ(20px);">
                            <div style="background:#f8fafc;padding:14px 18px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;justify-content:space-between;">
                                <div style="display:flex;gap:6px;">
                                    <div style="width:10px;height:10px;border-radius:50%;background:#EA4335;"></div>
                                    <div style="width:10px;height:10px;border-radius:50%;background:#FBBC05;"></div>
                                    <div style="width:10px;height:10px;border-radius:50%;background:#34A853;"></div>
                                </div>
                                <span style="font-size:0.72rem;color:#94a3b8;font-weight:500;">jobmatch.ai/dashboard</span>
                            </div>
                            <div style="padding:22px;">
                                <div style="font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">ATS SCORE</div>
                                <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:12px;">
                                    <span style="font-size:3rem;font-weight:800;color:var(--m3-on-bg);line-height:1;">87</span>
                                    <span style="font-size:1rem;color:#94a3b8;">/100</span>
                                </div>
                                <div style="height:8px;width:100%;background:#f1f5f9;border-radius:100px;overflow:hidden;margin-bottom:16px;">
                                    <div style="height:100%;width:87%;background:#4285F4;border-radius:100px;"></div>
                                </div>
                                <div style="font-size:0.85rem;font-weight:600;color:var(--m3-on-bg);margin-bottom:16px;">
                                    <span style="color:#34A853;">✓</span> CV Optimized — Product Manager Role
                                </div>
                                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;">
                                    <div style="background:#f8fafc;border-radius:10px;padding:10px;">
                                        <div style="font-size:0.68rem;font-weight:700;color:#64748b;margin-bottom:4px;">Keywords</div>
                                        <div style="font-size:0.9rem;font-weight:800;color:#34A853;">92%</div>
                                    </div>
                                    <div style="background:#f8fafc;border-radius:10px;padding:10px;">
                                        <div style="font-size:0.68rem;font-weight:700;color:#64748b;margin-bottom:4px;">Experience</div>
                                        <div style="font-size:0.9rem;font-weight:800;color:#FBBC05;">78%</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


        # ─── Problem Statement ───
        st.markdown(
            """
            <div style="background:var(--m3-surface);border-top:var(--m3-glass-border);border-bottom:var(--m3-glass-border);padding:60px 20px;margin-top:60px;text-align:center;font-family:'Inter',sans-serif;">
                <span style="display:inline-block;border-radius:100px;background:rgba(234,67,53,0.08);padding:6px 16px;font-size:0.72rem;font-weight:700;color:#EA4335;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:16px;">Real Talk</span>
                <h2 style="font-size:2.2rem;font-weight:800;color:var(--m3-on-bg);margin:0 0 18px 0;">75% CV Tidak Pernah Dibaca Manusia</h2>
                <p style="font-size:1.05rem;color:var(--m3-on-surface-variant);max-width:760px;margin:0 auto;line-height:1.65;">
                    Mayoritas perusahaan menggunakan Applicant Tracking System (ATS) untuk menyaring CV secara otomatis sebelum HRD melihatnya. Format salah, keyword hilang, atau struktur berantakan bisa bikin CV kamu <strong style="color:#EA4335;">auto-rejected</strong> — padahal kualifikasinya cocok.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ─── Features ───
        st.markdown(
            """
            <div style="max-width:1100px;margin:80px auto;padding:0 20px;font-family:'Inter',sans-serif;">
                <div style="text-align:center;margin-bottom:50px;">
                    <h2 style="font-size:2.2rem;font-weight:800;color:#0f172a;margin:0 0 10px 0;">Semua yang Kamu Butuhkan untuk <span style="color:#4285F4;">Lolos Interview</span></h2>
                    <p style="color:#64748b;font-size:1rem;margin:0;">4 fitur AI terpadu, dirancang khusus untuk pasar kerja Indonesia.</p>
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:24px;">
                    <div class="jm-feature-card">
                        <div class="jm-feature-icon" style="background:rgba(66,133,244,0.08);">📄</div>
                        <div style="width:100%;">
                            <p class="jm-feature-title">ATS Score Check</p>
                            <p class="jm-feature-desc">Upload CV, get instant compatibility score lengkap dengan breakdown dan rekomendasi improvement.</p>
                        </div>
                    </div>
                    <div class="jm-feature-card">
                        <div class="jm-feature-icon" style="background:rgba(251,188,5,0.08);">✨</div>
                        <div style="width:100%;">
                            <p class="jm-feature-title">Smart CV Builder</p>
                            <p class="jm-feature-desc">Scan CV lama kamu (even dari foto atau PDF berantakan) — auto-rapikan jadi format yang ATS-friendly.</p>
                        </div>
                    </div>
                    <div class="jm-feature-card">
                        <div class="jm-feature-icon" style="background:rgba(52,168,83,0.08);">💬</div>
                        <div style="width:100%;">
                            <p class="jm-feature-title">AI Mock Interview</p>
                            <p class="jm-feature-desc">Practice real-time sama AI interviewer — dapet feedback on tone, delivery, sampai konten jawaban kamu.</p>
                        </div>
                    </div>
                    <div class="jm-feature-card">
                        <div class="jm-feature-icon" style="background:rgba(234,67,53,0.08);">📈</div>
                        <div style="width:100%;">
                            <p class="jm-feature-title">Skill Gap Analysis</p>
                            <p class="jm-feature-desc">Tau exactly skill apa yang kurang buat role incaran, plus roadmap buat level up.</p>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ─── How It Works ───
        st.markdown(
            """
            <div style="background:#f8fafc;border-top:1px solid #f1f5f9;border-bottom:1px solid #f1f5f9;padding:80px 20px;font-family:'Inter',sans-serif;">
                <div style="max-width:1100px;margin:0 auto;">
                    <div style="text-align:center;margin-bottom:50px;">
                        <span style="display:inline-block;border-radius:100px;background:rgba(52,168,83,0.08);padding:6px 16px;font-size:0.72rem;font-weight:700;color:#34A853;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:14px;">How It Works</span>
                        <h2 style="font-size:2.2rem;font-weight:800;color:#0f172a;margin:0;">3 Langkah, <span style="color:#4285F4;">Tanpa Ribet</span></h2>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;text-align:center;">
                        <div style="padding:28px;background:white;border-radius:20px;border:1px solid #e2e8f0;box-shadow:0 4px 15px rgba(0,0,0,0.02);">
                            <div style="width:56px;height:56px;background:rgba(66,133,244,0.08);border-radius:16px;display:grid;place-items:center;margin:0 auto 18px auto;font-size:1.4rem;position:relative;">📤<span style="position:absolute;-top:8px;-right:8px;width:22px;height:22px;background:white;border-radius:50%;display:grid;place-items:center;font-size:0.7rem;font-weight:800;color:#4285F4;box-shadow:0 2px 6px rgba(0,0,0,0.1);">1</span></div>
                            <h3 style="font-size:1.15rem;font-weight:700;color:#0f172a;margin:0 0 10px 0;">Upload CV Kamu</h3>
                            <p style="color:#64748b;font-size:0.88rem;margin:0;line-height:1.55;">PDF atau foto — semua format bisa kami proses otomatis.</p>
                        </div>
                        <div style="padding:28px;background:white;border-radius:20px;border:1px solid #e2e8f0;box-shadow:0 4px 15px rgba(0,0,0,0.02);">
                            <div style="width:56px;height:56px;background:rgba(52,168,83,0.08);border-radius:16px;display:grid;place-items:center;margin:0 auto 18px auto;font-size:1.4rem;position:relative;">📊<span style="position:absolute;-top:8px;-right:8px;width:22px;height:22px;background:white;border-radius:50%;display:grid;place-items:center;font-size:0.7rem;font-weight:800;color:#34A853;box-shadow:0 2px 6px rgba(0,0,0,0.1);">2</span></div>
                            <h3 style="font-size:1.15rem;font-weight:700;color:#0f172a;margin:0 0 10px 0;">Cek Skor ATS</h3>
                            <p style="color:#64748b;font-size:0.88rem;margin:0;line-height:1.55;">Analisis mendalam plus rekomendasi perbaikan yang actionable dan spesifik.</p>
                        </div>
                        <div style="padding:28px;background:white;border-radius:20px;border:1px solid #e2e8f0;box-shadow:0 4px 15px rgba(0,0,0,0.02);">
                            <div style="width:56px;height:56px;background:rgba(234,67,53,0.08);border-radius:16px;display:grid;place-items:center;margin:0 auto 18px auto;font-size:1.4rem;position:relative;">🎤<span style="position:absolute;-top:8px;-right:8px;width:22px;height:22px;background:white;border-radius:50%;display:grid;place-items:center;font-size:0.7rem;font-weight:800;color:#EA4335;box-shadow:0 2px 6px rgba(0,0,0,0.1);">3</span></div>
                            <h3 style="font-size:1.15rem;font-weight:700;color:#0f172a;margin:0 0 10px 0;">Latihan Interview</h3>
                            <p style="color:#64748b;font-size:0.88rem;margin:0;line-height:1.55;">Sampai kamu beneran interview-ready dan percaya diri menghadapi rekruter.</p>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ─── Stats ───
        st.markdown(
            """
            <div class="jm-landing-stripe">
                <div class="jm-landing-stripe-stat">
                    <div class="jm-landing-stripe-num">10,000+</div>
                    <div class="jm-landing-stripe-label">CV Dianalisis</div>
                </div>
                <div class="jm-landing-stripe-stat">
                    <div class="jm-landing-stripe-num">85%</div>
                    <div class="jm-landing-stripe-label">Peningkatan Pass Rate</div>
                </div>
                <div class="jm-landing-stripe-stat">
                    <div class="jm-landing-stripe-num">500+</div>
                    <div class="jm-landing-stripe-label">Lowongan Kerja Aktif</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ─── Testimonials ───
        st.markdown(
            """
            <div style="max-width:1100px;margin:80px auto;padding:0 20px;font-family:'Inter',sans-serif;">
                <div style="text-align:center;margin-bottom:50px;">
                    <span style="display:inline-block;border-radius:100px;background:rgba(251,188,5,0.1);padding:6px 16px;font-size:0.72rem;font-weight:700;color:#b58600;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:14px;">Loved by Job Seekers</span>
                    <h2 style="font-size:2.2rem;font-weight:800;color:#0f172a;margin:0;">Kisah Nyata, <span style="color:#4285F4;">Offer Nyata</span></h2>
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;">
                    <div class="jm-feature-card" style="flex-direction:column;align-items:flex-start;">
                        <div style="display:flex;gap:4px;margin-bottom:14px;">⭐⭐⭐⭐⭐</div>
                        <p style="color:#475569;font-size:0.92rem;font-style:italic;line-height:1.65;margin:0 0 20px 0 !important;">"CV gue di-ghost 20+ perusahaan. Setelah pakai JobMatch AI, ATS score naik dari 42 ke 89. Minggu depannya langsung 3 interview call!"</p>
                        <div style="display:flex;align-items:center;gap:12px;margin-top:auto;border-top:1px solid #f1f5f9;padding-top:16px;width:100%;">
                            <div style="width:42px;height:42px;border-radius:50%;background:#4285F4;color:white;display:grid;place-items:center;font-weight:700;font-size:0.85rem;">RP</div>
                            <div><div style="font-size:0.88rem;font-weight:700;color:#0f172a;">Rania Putri</div><div style="font-size:0.75rem;color:#64748b;">Fresh Graduate · UI Designer</div></div>
                        </div>
                    </div>
                    <div class="jm-feature-card" style="flex-direction:column;align-items:flex-start;">
                        <div style="display:flex;gap:4px;margin-bottom:14px;">⭐⭐⭐⭐⭐</div>
                        <p style="color:#475569;font-size:0.92rem;font-style:italic;line-height:1.65;margin:0 0 20px 0 !important;">"Mock interview-nya seriously game-changer. Feedback-nya detail sampai ke intonasi. Confidence naik banget pas interview beneran."</p>
                        <div style="display:flex;align-items:center;gap:12px;margin-top:auto;border-top:1px solid #f1f5f9;padding-top:16px;width:100%;">
                            <div style="width:42px;height:42px;border-radius:50%;background:#34A853;color:white;display:grid;place-items:center;font-weight:700;font-size:0.85rem;">MS</div>
                            <div><div style="font-size:0.88rem;font-weight:700;color:#0f172a;">Michael Santoso</div><div style="font-size:0.75rem;color:#64748b;">Product Manager</div></div>
                        </div>
                    </div>
                    <div class="jm-feature-card" style="flex-direction:column;align-items:flex-start;">
                        <div style="display:flex;gap:4px;margin-bottom:14px;">⭐⭐⭐⭐⭐</div>
                        <p style="color:#475569;font-size:0.92rem;font-style:italic;line-height:1.65;margin:0 0 20px 0 !important;">"Skill gap analysis-nya spot on. Tau exactly course apa yang harus gue ambil buat switch career ke data role."</p>
                        <div style="display:flex;align-items:center;gap:12px;margin-top:auto;border-top:1px solid #f1f5f9;padding-top:16px;width:100%;">
                            <div style="width:42px;height:42px;border-radius:50%;background:#EA4335;color:white;display:grid;place-items:center;font-weight:700;font-size:0.85rem;">DA</div>
                            <div><div style="font-size:0.88rem;font-weight:700;color:#0f172a;">Dinda Ayu</div><div style="font-size:0.75rem;color:#64748b;">Data Analyst · Ex-Big 4</div></div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ─── Final CTA ───
        st.markdown(
            """
            <div style="max-width:960px;margin:40px auto 30px auto;padding:0 20px;font-family:'Inter',sans-serif;">
                <div style="background:#0f172a;border-radius:32px;padding:60px 40px;text-align:center;position:relative;overflow:hidden;">
                    <div style="position:absolute;top:0;right:0;width:250px;height:250px;background:#4285F4;opacity:0.12;border-radius:50%;filter:blur(80px);"></div>
                    <div style="position:absolute;bottom:0;left:0;width:250px;height:250px;background:#34A853;opacity:0.12;border-radius:50%;filter:blur(80px);"></div>
                    <h2 style="font-size:2.4rem;font-weight:800;color:white;margin:0 0 14px 0;position:relative;letter-spacing:-0.02em;">Stop Guessing Why Your CV Gets Rejected</h2>
                    <p style="color:#94a3b8;font-size:1.1rem;max-width:560px;margin:0 auto 20px auto;line-height:1.65;position:relative;">Ribuan job seekers udah pakai JobMatch AI buat pass first screening.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _cta1, _cta_b1, _cta_b2, _cta3 = st.columns([0.8, 1.2, 1.3, 0.8])
        with _cta_b1:
            if st.button("Start Free Now  →", type="primary", use_container_width=True, key="final_cta_btn"):
                st.login("google")
        with _cta_b2:
            if st.button("Sign in with Google", type="secondary", use_container_width=True, key="final_google_btn", icon=":material/login:"):
                st.login("google")

        st.markdown(
            """
            <div style="text-align:center;margin-top:16px;margin-bottom:40px;font-family:'Inter',sans-serif;color:#64748b;font-size:0.88rem;">
                Start for free · No credit card required
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ─── Footer ───
        st.markdown(
            """
            <div class="jm-landing-footer" style="margin-top:40px;">
                <span>© 2026 JobMatch AI</span>
                <span>Tentang Kami</span>
                <span>Fitur</span>
                <span>Cara Kerja</span>
                <span>Kebijakan Privasi</span>
                <span>Hubungi Kami</span>
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
