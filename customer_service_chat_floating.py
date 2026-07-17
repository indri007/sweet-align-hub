"""
Customer Service Chatbot Module - JobMatch AI (Floating Widget)
=================================================================
Konsisten dengan pola google-genai SDK yang sudah dipakai di project ini
(config.py -> get_gemini_client(), lihat juga agents/career_agent.py).
"""

import streamlit as st
import config
from google.genai import types


SYSTEM_PROMPT = """
Kamu adalah "Asisten JobMatch AI", customer service resmi untuk aplikasi JobMatch AI.

TENTANG JOBMATCH AI:
- CV Review: menganalisis CV yang diunggah pengguna dan memberi masukan perbaikan.
- Free download template CV yang ATS-friendly.
- Job Recommendations: merekomendasikan lowongan kerja relevan berdasarkan CV/profil pengguna.
- Fitur yang sedang dikembangkan: mock interview (berbasis AI) dan CV processor yang lebih canggih.

ATURAN UTAMA:
1. Jawab HANYA seputar JobMatch AI: cara pakai fitur, alur upload CV, hasil analisis,
   rekomendasi kerja, template CV, akun/login, dan hal teknis dasar terkait aplikasi ini.
2. Jika pertanyaan di luar konteks, jangan menjawab topik tersebut.
   Alihkan dengan sopan kembali ke konteks JobMatch AI. Contoh gaya redirect:
   "Wah, itu di luar topik yang bisa aku bantu ya. Tapi kalau soal CV atau
   pencarian kerja di JobMatch AI, aku siap bantu banget nih!"
3. Gunakan bahasa profesional namun hangat dan manusiawi (humanistic) — seperti
   customer service ramah, bukan robot kaku. Hindari jawaban template yang mekanis.
4. Jawaban singkat, jelas, langsung ke poin.
5. Jika tidak tahu jawaban pasti, jangan mengarang. Arahkan ke tim support resmi.
6. Jangan pernah membocorkan detail internal (arsitektur sistem, API key, infrastruktur).
7. Gunakan Bahasa Indonesia sebagai default, kecuali pengguna menulis dalam
   Bahasa Inggris — maka balas dalam Bahasa Inggris juga.
"""


def _inject_floating_css():
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"]:has(div.cs-widget-marker),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div.cs-widget-marker) {
            position: fixed !important;
            bottom: 90px;
            right: 20px;
            width: 340px;
            max-height: 480px;
            z-index: 9999;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.18);
            padding: 14px 14px 8px 14px;
            overflow-y: auto;
        }

        div[data-testid="stVerticalBlock"]:has(div.cs-toggle-marker),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div.cs-toggle-marker) {
            position: fixed !important;
            bottom: 20px;
            right: 20px;
            z-index: 9998;
            width: auto !important;
        }

        .cs-toggle-marker + div button {
            border-radius: 50% !important;
            width: 56px;
            height: 56px;
            font-size: 22px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.25);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .cs-toggle-marker + div button span[data-testid="stIconMaterial"] {
            font-size: 26px !important;
        }

        .cs-header {
            font-weight: 600;
            font-size: 15px;
            margin-bottom: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _ask_cs_bot(chat_history: list, user_message: str) -> str:
    if not config.is_gemini_configured():
        return (
            "Maaf, fitur chat CS belum aktif saat ini. "
            "Silakan hubungi tim support kami secara langsung ya."
        )

    try:
        client = config.get_gemini_client()

        contents = []
        for msg in chat_history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                top_p=0.9,
                top_k=40,
                max_output_tokens=300,
            ),
        )
        return response.text

    except Exception:
        return (
            "Maaf, sepertinya ada kendala teknis sesaat. "
            "Coba tanya lagi sebentar lagi ya."
        )


def render_cs_chatbot():
    _inject_floating_css()

    if "cs_open" not in st.session_state:
        st.session_state.cs_open = False
    if "cs_messages" not in st.session_state:
        st.session_state.cs_messages = []

    with st.container():
        st.markdown('<div class="cs-toggle-marker"></div>', unsafe_allow_html=True)
        if st.session_state.cs_open:
            btn_clicked = st.button("", icon=":material/close:", key="cs_toggle_btn")
        else:
            btn_clicked = st.button("", icon=":material/support_agent:", key="cs_toggle_btn")
        if btn_clicked:
            st.session_state.cs_open = not st.session_state.cs_open
            st.rerun()

    if st.session_state.cs_open:
        with st.container():
            st.markdown('<div class="cs-widget-marker"></div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="cs-header">💬 Customer Service — JobMatch AI</div>',
                unsafe_allow_html=True,
            )
            st.caption("Tanya seputar CV Review, Job Recommendations, atau fitur lainnya.")

            with st.container(height=280):
                for msg in st.session_state.cs_messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            user_input = st.chat_input("Tulis pertanyaanmu...", key="cs_input")

            if user_input:
                st.session_state.cs_messages.append({"role": "user", "content": user_input})
                reply = _ask_cs_bot(st.session_state.cs_messages[:-1], user_input)
                st.session_state.cs_messages.append({"role": "assistant", "content": reply})
                st.rerun()
