"""
Step D — Konsultasi Karir (career chat).

Extracted verbatim from app.py during modularization (Tahap 3).
No behavior change from the original inline block.
"""

import streamlit as st

import config
from nav import next_step, prev_step


def render_step_d():
    st.markdown(
        """<div class="hero-container animate-fade-in">
            <div class="hero-title">💬 Konsultasi Karir</div>
            <div class="hero-subtitle">
                Diskusikan cita-cita dan tujuan karir kamu dengan AI Career Consultant
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    if not config.is_gemini_configured():
        st.warning(
            "⚠️ Fitur ini membutuhkan Gemini API key. Tambahkan `GEMINI_API_KEY` di file `.env`",
            icon="🔑",
        )
    else:
        # Display chat history
        for msg in st.session_state.career_chat_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-user">🧑 {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="chat-ai">🤖 {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )

        # Welcome message if no history
        if not st.session_state.career_chat_history:
            st.markdown(
                """<div class="chat-ai">
                    🤖 Halo! Saya AI Career Consultant kamu. Saya sudah membaca CV kamu.<br><br>
                    Silakan ceritakan tentang:<br>
                    • 🎯 Cita-cita atau tujuan karir kamu<br>
                    • 🤔 Keraguan tentang pilihan karir<br>
                    • 📈 Skill yang ingin dikembangkan<br>
                    • 💡 Atau apapun tentang karir kamu!
                </div>""",
                unsafe_allow_html=True,
            )

        # Chat input
        user_input = st.chat_input("Ketik pesan kamu di sini...")

        if user_input:
            # Add user message
            st.session_state.career_chat_history.append(
                {"role": "user", "content": user_input}
            )

            # Get AI response
            with st.spinner("🤖 AI sedang berpikir..."):
                from agents.career_agent import get_career_response
                result = get_career_response(
                    cv_text=st.session_state.cv_text,
                    chat_history=st.session_state.career_chat_history[:-1],  # exclude last
                    user_message=user_input,
                )

                if result["available"] and result["response"]:
                    st.session_state.career_chat_history.append(
                        {"role": "assistant", "content": result["response"]}
                    )
                else:
                    st.session_state.career_chat_history.append(
                        {"role": "assistant", "content": "Maaf, terjadi kesalahan. Coba lagi."}
                    )

            st.rerun()

        # Clear chat button
        if st.session_state.career_chat_history:
            if st.button("🗑️ Hapus Riwayat Chat"):
                st.session_state.career_chat_history = []
                st.rerun()

    # Navigation
    st.markdown("---")
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_l:
        if st.button("← Kembali", use_container_width=True):
            prev_step()
            st.rerun()
    with col_r:
        if st.button("Mock Interview →", type="primary", use_container_width=True):
            next_step()
            st.rerun()
