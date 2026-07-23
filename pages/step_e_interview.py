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
                if st.button("🎬 Mulai Interview Sekarang", type="primary"):
                    with st.spinner("🤖 HR sedang mempersiapkan interview..."):
                        from agents.interview_agent import start_interview, get_active_question
                        try:
                            # Start session (FR-15) via wrapper
                            session = start_interview(st.session_state.cv_text, job)
                            st.session_state.interview_session = session
                            
                            first_q = get_active_question(session)
                            
                            st.session_state.interview_history = [
                                {"role": "assistant", "content": first_q}
                            ]
                            st.session_state.interview_started = True
                            st.session_state.transcript_saved = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal memulai interview: {e}")
            else:
                # Display interview conversation
                for msg in st.session_state.interview_history:
                    if msg["role"] == "assistant":
                        st.markdown(
                            f'<div class="chat-ai">🤵 HR: {msg["content"]}</div>',
                            unsafe_allow_html=True,
                        )

                        # TTS for voice mode
                        if mode == "🎙️ Voice" and msg == st.session_state.interview_history[-1]:
                            try:
                                from agents.interview_agent import text_to_speech
                                audio_bytes = text_to_speech(msg["content"])
                                if audio_bytes:
                                    st.audio(audio_bytes, format="audio/mp3")
                            except Exception:
                                pass

                    else:
                        st.markdown(
                            f'<div class="chat-user">🧑 Kamu: {msg["content"]}</div>',
                            unsafe_allow_html=True,
                        )

                # Input area
                if mode == "💬 Text":
                    answer = st.chat_input("Ketik jawaban kamu...")
                    if answer:
                        st.session_state.interview_history.append(
                            {"role": "user", "content": answer}
                        )
                        with st.spinner("🤵 HR sedang mengevaluasi jawaban..."):
                            from agents.interview_agent import handle_candidate_answer
                            
                            session = st.session_state.get("interview_session")
                            if session:
                                try:
                                    next_q = handle_candidate_answer(
                                        session,
                                        jawaban_user=answer,
                                    )
                                    
                                    if next_q:
                                        st.session_state.interview_history.append(
                                            {"role": "assistant", "content": next_q}
                                        )
                                    elif not st.session_state.get("transcript_saved", False):
                                        st.session_state.interview_history.append(
                                            {"role": "assistant", "content": "🎉 Wawancara selesai! Sedang menyusun laporan evaluasi..."}
                                        )
                                        try:
                                            from agents.interview_agent import evaluate_interview
                                            from database import DatabaseManager
                                            import dataclasses
                                            
                                            eval_res = evaluate_interview(session)
                                            
                                            # Simpan transkrip ke database FR-17
                                            try:
                                                db = DatabaseManager()
                                                email = getattr(st.user, "email", "unknown@example.com")
                                                session_dict = dataclasses.asdict(session)
                                                db.save_hrd_transcript(session_dict, email)
                                                st.session_state.transcript_saved = True
                                            except Exception as db_err:
                                                st.error(f"⚠️ Gagal menyimpan riwayat wawancara ke database: {db_err}")

                                            eval_text = "### 📊 Hasil Evaluasi Interview\n\n"
                                            for ev in eval_res.get("evaluasi", []):
                                                eval_text += f"**{ev.get('kompetensi', 'Kompetensi')}** (Label: {ev.get('label', '-')})\n"
                                                eval_text += f"> {ev.get('feedback', '')}\n\n"
                                            eval_text += f"**Kesimpulan Umum:**\n{eval_res.get('kesimpulan_umum', '')}"
                                            st.session_state.interview_history.append(
                                                {"role": "assistant", "content": eval_text}
                                            )
                                        except Exception as e:
                                            st.session_state.interview_history.append(
                                                {"role": "assistant", "content": f"⚠️ Gagal memuat evaluasi: {e}"}
                                            )
                                except Exception as e:
                                    st.error(f"Terjadi kesalahan: {e}")
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
                                    from agents.interview_agent import (
                                        transcribe_audio,
                                        handle_candidate_answer,
                                    )
                                    
                                    transcribed = transcribe_audio(audio_bytes)
                                    st.info(f"📝 Transcribed: {transcribed}")

                                    st.session_state.interview_history.append(
                                        {"role": "user", "content": transcribed}
                                    )

                                    session = st.session_state.get("interview_session")
                                    if session:
                                        try:
                                            next_q = handle_candidate_answer(
                                                session,
                                                jawaban_user=transcribed,
                                            )
                                            if next_q:
                                                st.session_state.interview_history.append(
                                                    {"role": "assistant", "content": next_q}
                                                )
                                            elif not st.session_state.get("transcript_saved", False):
                                                st.session_state.interview_history.append(
                                                    {"role": "assistant", "content": "🎉 Wawancara selesai! Sedang menyusun laporan evaluasi..."}
                                                )
                                                try:
                                                    from agents.interview_agent import evaluate_interview
                                                    from database import DatabaseManager
                                                    import dataclasses
                                                    
                                                    eval_res = evaluate_interview(session)
                                                    
                                                    # Simpan transkrip ke database FR-17
                                                    try:
                                                        db = DatabaseManager()
                                                        email = getattr(st.user, "email", "unknown@example.com")
                                                        session_dict = dataclasses.asdict(session)
                                                        db.save_hrd_transcript(session_dict, email)
                                                        st.session_state.transcript_saved = True
                                                    except Exception as db_err:
                                                        st.error(f"⚠️ Gagal menyimpan riwayat wawancara ke database: {db_err}")

                                                    eval_text = "### 📊 Hasil Evaluasi Interview\n\n"
                                                    for ev in eval_res.get("evaluasi", []):
                                                        eval_text += f"**{ev.get('kompetensi', 'Kompetensi')}** (Label: {ev.get('label', '-')})\n"
                                                        eval_text += f"> {ev.get('feedback', '')}\n\n"
                                                    eval_text += f"**Kesimpulan Umum:**\n{eval_res.get('kesimpulan_umum', '')}"
                                                    st.session_state.interview_history.append(
                                                        {"role": "assistant", "content": eval_text}
                                                    )
                                                except Exception as e:
                                                    st.session_state.interview_history.append(
                                                        {"role": "assistant", "content": f"⚠️ Gagal memuat evaluasi: {e}"}
                                                    )
                                        except Exception as e:
                                            st.error(f"Terjadi kesalahan: {e}")
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
                    st.session_state.transcript_saved = False
                    st.session_state.interview_history = []
                    st.session_state.interview_session = None
                    st.rerun()
            with col2:
                if st.button("🔄 Ganti Posisi"):
                    st.session_state.interview_job = None
                    st.session_state.interview_started = False
                    st.session_state.transcript_saved = False
                    st.session_state.interview_history = []
                    st.session_state.interview_session = None
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
