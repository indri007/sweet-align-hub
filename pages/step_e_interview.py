"""
Step E — Mock Interview.

Extracted verbatim from app.py during modularization (Tahap 3).
No behavior change from the original inline block.
"""

import streamlit as st

import config
from nav import prev_step


def render_step_e():
    st.markdown(
        """<div class="hero-container animate-fade-in">
            <div class="hero-title">🎤 Mock Interview</div>
            <div class="hero-subtitle">
                Simulasi interview dengan AI sebagai HR Interviewer. Pilih mode text atau voice.
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
        # Job selection for interview
        if not st.session_state.interview_job:
            st.markdown("### 🎯 Pilih Posisi untuk Interview")

            if st.session_state.job_matches:
                job_options = {}
                for j in st.session_state.job_matches:
                    meta = j.get("metadata", {})
                    label = f"{meta.get('job_title', 'N/A')} — {meta.get('company_name', 'N/A')}"
                    job_options[label] = {
                        "job_title": meta.get("job_title", ""),
                        "company_name": meta.get("company_name", ""),
                        "job_description": j.get("document", ""),
                    }

                selected = st.selectbox("Pilih lowongan:", list(job_options.keys()))
                if st.button("🎬 Mulai Interview", type="primary"):
                    st.session_state.interview_job = job_options[selected]
                    st.rerun()
            else:
                st.info("💡 Upload CV dan lihat rekomendasi dulu (Step A & B) untuk memilih posisi interview.")

                # Manual input option
                st.markdown("**Atau input manual:**")
                manual_title = st.text_input("Job Title", placeholder="contoh: Data Analyst")
                manual_company = st.text_input("Company Name", placeholder="contoh: PT ABC")
                manual_desc = st.text_area("Job Description (opsional)", placeholder="Deskripsi pekerjaan...")

                if manual_title and st.button("🎬 Mulai Interview", type="primary"):
                    st.session_state.interview_job = {
                        "job_title": manual_title,
                        "company_name": manual_company or "Unknown Company",
                        "job_description": manual_desc or "N/A",
                    }
                    st.rerun()

        else:
            # Show interview info
            job = st.session_state.interview_job
            st.markdown(
                f"""<div class="glass-card">
                    <h4 style="color:var(--accent-blue);">🎯 Posisi: {job['job_title']}</h4>
                    <p style="color:var(--text-secondary);">🏢 {job['company_name']}</p>
                </div>""",
                unsafe_allow_html=True,
            )

            # Mode selection
            mode = st.radio(
                "Mode Interview:",
                ["💬 Text", "🎙️ Voice"],
                horizontal=True,
            )

            # Start interview if not started
            if not st.session_state.interview_started:
                st.info("💡 Karena API Key Gemini saat ini terkena limit (429), Anda bisa menekan tombol Preview di bawah untuk melihat simulasi tampilannya.")
                if st.button("👁️ Preview Tampilan UI (Tanpa Kuota API)", type="secondary"):
                    st.session_state.interview_history = [
                        {"role": "assistant", "content": "Halo, saya Leonardo, HR Manager di sini. Saya telah membaca CV Anda dengan teliti. Mari kita mulai wawancara ini. Coba ceritakan satu tantangan teknis paling rumit yang pernah Anda selesaikan."},
                        {"role": "user", "content": "Tantangan terbesar saya adalah ketika server utama mengalami *downtime* tak terduga selama 3 jam. Saya harus berkoordinasi dengan tim jaringan sambil melakukan mitigasi data."},
                        {"role": "assistant", "content": "Langkah mitigasi yang sangat responsif! Dalam situasi panik seperti itu, bagaimana cara Anda mengkomunikasikan masalahnya kepada klien yang terdampak?"}
                    ]
                    st.session_state.interview_started = True
                    st.rerun()
                
                if st.button("🎬 Mulai Interview Sekarang", type="primary"):
                    with st.spinner("👨‍💼 Leonardo sedang mempersiapkan interview..."):
                        try:
                            from agents.interview_agent import start_interview
                            result = start_interview(st.session_state.cv_text, job)
                            if result["available"] and result["response"]:
                                st.session_state.interview_history = [
                                    {"role": "assistant", "content": result["response"]}
                                ]
                                st.session_state.interview_started = True
                                st.rerun()
                            else:
                                st.error("❌ Gagal memulai interview. Silakan coba lagi.")
                        except Exception as e:
                            st.error(f"❌ Terjadi kesalahan saat memulai interview: {e}")
            else:
                # Display interview conversation
                for msg in st.session_state.interview_history:
                    if msg["role"] == "assistant":
                        with st.chat_message("Leonardo", avatar="assets/leonardo.jpg"):
                            st.write(msg["content"])
                            # TTS for voice mode
                            if mode == "🎙️ Voice" and msg == st.session_state.interview_history[-1]:
                                try:
                                    from agents.interview_agent import text_to_speech
                                    audio_bytes = text_to_speech(msg["content"])
                                    if audio_bytes:
                                        st.audio(audio_bytes, format="audio/mp3")
                                except Exception as e:
                                    st.error(f"Gagal memutar audio: {e}")
                    else:
                        with st.chat_message("Anda", avatar="🧑"):
                            st.write(msg["content"])

                # Input area
                if mode == "💬 Text":
                    answer = st.chat_input("Ketik jawaban kamu...")
                    if answer:
                        st.session_state.interview_history.append(
                            {"role": "user", "content": answer}
                        )
                        with st.spinner("👨‍💼 Leonardo sedang mengevaluasi jawaban..."):
                            try:
                                from agents.interview_agent import continue_interview
                                result = continue_interview(
                                    st.session_state.cv_text,
                                    job,
                                    st.session_state.interview_history[:-1],
                                    answer,
                                )
                                if result["available"] and result["response"]:
                                    st.session_state.interview_history.append(
                                        {"role": "assistant", "content": result["response"]}
                                    )
                                else:
                                    st.error("❌ Gagal mendapatkan respon HR.")
                            except Exception as e:
                                st.error(f"❌ Terjadi kesalahan saat mengevaluasi jawaban: {e}")
                        st.rerun()

                else:  # Voice mode
                    st.markdown("### 🎙️ Rekam Jawaban")
                    try:
                        from audio_recorder_streamlit import audio_recorder
                        audio_bytes = audio_recorder(
                            text="Klik untuk mulai merekam",
                            recording_color="#f43f5e",
                            neutral_color="#00d4ff",
                            icon_size="2x",
                        )
                        if audio_bytes:
                            st.audio(audio_bytes, format="audio/wav")
                            if st.button("📤 Kirim Jawaban", type="primary"):
                                with st.spinner("🎧 Transcribing audio..."):
                                    try:
                                        from agents.interview_agent import (
                                            transcribe_audio,
                                            continue_interview,
                                        )
                                        transcribed = transcribe_audio(audio_bytes)
                                        st.info(f"📝 Transcribed: {transcribed}")

                                        st.session_state.interview_history.append(
                                            {"role": "user", "content": transcribed}
                                        )

                                        result = continue_interview(
                                            st.session_state.cv_text,
                                            job,
                                            st.session_state.interview_history[:-1],
                                            transcribed,
                                        )
                                        if result["available"] and result["response"]:
                                            st.session_state.interview_history.append(
                                                {"role": "assistant", "content": result["response"]}
                                            )
                                        else:
                                            st.error("❌ Gagal mendapatkan respon HR.")
                                    except Exception as e:
                                        st.error(f"❌ Terjadi kesalahan saat memproses audio: {e}")
                                    st.rerun()
                    except ImportError:
                        st.warning("📦 Package `audio-recorder-streamlit` belum terinstall.")
                        st.code("pip install audio-recorder-streamlit")
                        st.info("Gunakan mode Text untuk sementara.")

            # Reset interview
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reset Interview"):
                    st.session_state.interview_started = False
                    st.session_state.interview_history = []
                    st.rerun()
            with col2:
                if st.button("🔄 Ganti Posisi"):
                    st.session_state.interview_job = None
                    st.session_state.interview_started = False
                    st.session_state.interview_history = []
                    st.rerun()

    # Navigation
    st.markdown("---")
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_l:
        if st.button("← Kembali", use_container_width=True):
            prev_step()
            st.rerun()
    with col_r:
        st.markdown(
            """<div style="text-align:center; padding:10px;">
                <span style="color:var(--accent-emerald); font-weight:600;">
                    🎉 Ini step terakhir!
                </span>
            </div>""",
            unsafe_allow_html=True,
        )
