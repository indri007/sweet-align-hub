"""
Step C — Review CV.

Extracted verbatim from app.py during modularization (Tahap 3).
Patched: added error handling for AI calls, caching for generated
docx/pdf bytes (avoid regenerating on every Streamlit rerun), and
validation when "tailor CV" is checked but no job info is provided.
"""

import streamlit as st

import config
from nav import next_step, prev_step


def render_step_c():
    st.markdown(
        """<div class="hero-container animate-fade-in">
            <div class="hero-title">✍️ Review & Saran CV</div>
            <div class="hero-subtitle">
                AI akan menganalisis CV kamu dan memberikan feedback untuk meningkatkan kualitasnya
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
        tab1, tab2 = st.tabs(["📊 Feedback & Saran", "📝 Generate CV ATS"])

        # ── Tab 1: CV Feedback ──
        with tab1:
            if st.session_state.cv_feedback is None:
                if st.button("🤖 Analisis CV Saya", type="primary", use_container_width=True):
                    with st.spinner("🤖 AI sedang menganalisis CV kamu..."):
                        try:
                            from agents.cv_analyzer_agent import review_cv
                            result = review_cv(st.session_state.cv_text)
                            if result["available"] and result["feedback"]:
                                st.session_state.cv_feedback = result["feedback"]
                                st.rerun()
                            else:
                                st.error("❌ Gagal menganalisis CV. Coba lagi beberapa saat.")
                        except Exception as e:
                            st.error(f"❌ Terjadi kesalahan saat menganalisis CV: {e}")
            else:
                st.markdown(st.session_state.cv_feedback)

                if st.button("🔄 Analisis Ulang"):
                    st.session_state.cv_feedback = None
                    st.rerun()

        # ── Tab 2: ATS CV Generation ──
        with tab2:
            st.markdown(
                """<div class="glass-card">
                    <h4 style="color:var(--accent-emerald);">📝 Generate CV ATS-Friendly</h4>
                    <p style="font-size:0.9rem; color:var(--text-secondary);">
                        AI akan membuat versi CV kamu yang dioptimalkan untuk Applicant Tracking System (ATS).
                        Kamu bisa download hasilnya dalam format Word atau PDF.
                    </p>
                </div>""",
                unsafe_allow_html=True,
            )

            if st.session_state.ats_cv_text is None:
                st.markdown("#### 🎯 Kustomisasi CV (Opsional)")
                tailor_opt = st.checkbox("Sesuaikan CV dengan posisi & perusahaan yang dilamar", value=False)

                selected_job = None
                if tailor_opt:
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

                        selected_label = st.selectbox("Pilih posisi dari rekomendasi lowongan:", list(job_options.keys()))
                        selected_job = job_options[selected_label]
                    else:
                        st.info("💡 Tidak ada rekomendasi lowongan yang ditemukan. Masukkan informasi lowongan secara manual:")
                        man_title = st.text_input("Jabatan / Posisi", placeholder="contoh: Backend Developer")
                        man_company = st.text_input("Nama Perusahaan", placeholder="contoh: PT Maju Bersama")
                        man_desc = st.text_area("Deskripsi Pekerjaan (opsional)", placeholder="Kualifikasi, deskripsi tugas...")
                        if man_title:
                            selected_job = {
                                "job_title": man_title,
                                "company_name": man_company or "Unknown Company",
                                "job_description": man_desc or "N/A"
                            }

                st.markdown("#### 🌐 Pilih Bahasa CV ATS")
                lang_choice = st.radio(
                    "Bahasa output CV ATS:",
                    options=["auto", "id", "en"],
                    format_func=lambda x: {
                        "auto": "🔄 Otomatis (ikuti bahasa CV asli)",
                        "id": "🇮🇩 Bahasa Indonesia",
                        "en": "🇬🇧 English",
                    }[x],
                    horizontal=True,
                    label_visibility="collapsed",
                )

                if st.button(
                    "✨ Generate CV ATS",
                    type="primary",
                    use_container_width=True,
                    disabled=(tailor_opt and selected_job is None),
                ):
                    with st.spinner("✨ AI sedang membuat CV ATS-friendly..."):
                        try:
                            from agents.cv_analyzer_agent import generate_ats_cv
                            result = generate_ats_cv(st.session_state.cv_text, selected_job, language=lang_choice)
                            if result["available"] and result["ats_text"]:
                                st.session_state.ats_cv_text = result["ats_text"]
                                st.session_state.ats_docx_bytes = None
                                st.session_state.ats_pdf_bytes = None
                                st.rerun()
                            else:
                                st.error("❌ Gagal membuat CV ATS. Coba lagi beberapa saat.")
                        except Exception as e:
                            st.error(f"❌ Terjadi kesalahan saat membuat CV ATS: {e}")

                if tailor_opt and selected_job is None:
                    st.caption("⚠️ Isi jabatan/posisi dulu untuk mengaktifkan tombol generate.")
            else:
                st.markdown("### 📄 Preview CV ATS")
                st.text_area(
                    "ATS CV",
                    st.session_state.ats_cv_text,
                    height=400,
                    disabled=True,
                    label_visibility="collapsed",
                )

                # Download buttons
                st.markdown("### 📥 Download CV ATS")
                col1, col2 = st.columns(2)

                with col1:
                    try:
                        if st.session_state.get("ats_docx_bytes") is None:
                            from agents.cv_analyzer_agent import export_cv_to_docx
                            st.session_state.ats_docx_bytes = export_cv_to_docx(st.session_state.ats_cv_text)
                        st.download_button(
                            "📄 Download Word (.docx)",
                            data=st.session_state.ats_docx_bytes,
                            file_name="CV_ATS_Optimized.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(f"Error generating DOCX: {e}")

                with col2:
                    try:
                        if st.session_state.get("ats_pdf_bytes") is None:
                            from agents.cv_analyzer_agent import export_cv_to_pdf
                            st.session_state.ats_pdf_bytes = export_cv_to_pdf(st.session_state.ats_cv_text)
                        st.download_button(
                            "📑 Download PDF (.pdf)",
                            data=st.session_state.ats_pdf_bytes,
                            file_name="CV_ATS_Optimized.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(f"Error generating PDF: {e}")

                if st.button("🔄 Generate Ulang"):
                    st.session_state.ats_cv_text = None
                    st.session_state.ats_docx_bytes = None
                    st.session_state.ats_pdf_bytes = None
                    st.rerun()

    # Navigation
    st.markdown("---")
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_l:
        if st.button("← Kembali", use_container_width=True):
            prev_step()
            st.rerun()
    with col_r:
        if st.button("Konsultasi Karir →", type="primary", use_container_width=True):
            next_step()
            st.rerun()
