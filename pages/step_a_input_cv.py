"""
Step A — Input CV.

Extracted verbatim from app.py during modularization (Tahap 3).
No behavior change from the original inline block.
"""

import streamlit as st

import config
from cv_processor import extract_cv_text, get_file_info, validate_cv_file
from nav import next_step


def render_step_a():
    st.markdown(
        """<div class="hero-container animate-fade-in">
            <div class="hero-title">📄 Upload CV Kamu</div>
            <div class="hero-subtitle">
                Upload CV dalam format PDF atau Word untuk memulai analisis AI. 
                Kami akan mencocokkan profil kamu dengan ratusan lowongan pekerjaan.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Drag & drop CV kamu di sini",
            type=["pdf", "docx", "doc"],
            help="Format yang didukung: PDF, DOCX, DOC. Maksimum 5MB.",
            key="cv_uploader",
        )

        if uploaded_file is not None:
            # Validate size
            max_bytes = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
            if uploaded_file.size > max_bytes:
                st.error(f"❌ File terlalu besar. Maksimum {config.MAX_UPLOAD_SIZE_MB}MB.")
                st.stop()

            file_bytes = uploaded_file.getvalue()

            # Validate
            is_valid, error_msg = validate_cv_file(file_bytes, uploaded_file.name)

            if not is_valid:
                st.error(f"❌ {error_msg}")
            else:
                # Extract text
                with st.spinner("📖 Membaca CV kamu..."):
                    try:
                        from metrics import record_event, track_duration
                        import sentry_sdk
                        from logger import get_logger
                        logger = get_logger(__name__)
                        
                        file_ext = get_file_info(file_bytes, uploaded_file.name).get("format", "UNKNOWN")
                        with track_duration("cv_processing", format=file_ext):
                            cv_text = extract_cv_text(file_bytes, uploaded_file.name)
                        file_info = get_file_info(file_bytes, uploaded_file.name)

                        # Save to session state
                        st.session_state.cv_uploaded = True
                        st.session_state.cv_text = cv_text
                        st.session_state.cv_filename = uploaded_file.name
                        st.session_state.cv_file_info = file_info
                        st.session_state.cv_bytes = file_bytes

                        # --- CLONED SCORING LOGIC ---
                        # Automatically analyze CV and extract ATS score
                        if not st.session_state.get("cv_feedback"):
                            from agents.cv_analyzer_agent import review_cv
                            import re
                            result = review_cv(cv_text)
                            if result.get("available") and result.get("feedback"):
                                st.session_state.cv_feedback = result["feedback"]
                                match = re.search(r"ATS Score:\s*\[?(\d+)\]?", result["feedback"], re.IGNORECASE)
                                if match:
                                    st.session_state.ats_score = match.group(1)
                                else:
                                    st.session_state.ats_score = "N/A"

                        # Save profile to Aiven MySQL
                        user_email = getattr(st.user, "email", None)
                        if user_email:
                            try:
                                from database import DatabaseManager
                                db = DatabaseManager()
                                db.create_tables()
                                db.save_user_profile(
                                    email=user_email,
                                    name=getattr(st.user, "name", "User"),
                                    cv_text=cv_text,
                                    cv_filename=uploaded_file.name
                                )
                                logger.info("User profile saved", extra={"email": user_email})
                            except Exception as db_e:
                                logger.error("Failed to save user profile", extra={"error": str(db_e)})


                        record_event("cv_upload_success")
                        logger.info("CV processed", extra={"uploaded_filename": uploaded_file.name})
                        st.success("✅ CV berhasil di-upload dan dibaca!")

                    except Exception as e:
                        record_event("cv_upload_failure", reason=type(e).__name__)
                        logger.error("CV processing failed", extra={"err_msg": str(e), "cv_filename": uploaded_file.name})
                        sentry_sdk.capture_exception(e)
                        st.error(f"❌ Gagal membaca CV: {str(e)}")

    with col2:
        st.markdown(
            """<div class="glass-card">
                <h4 style="color:var(--accent-blue);">📋 Panduan</h4>
                <p style="font-size:0.85rem; color:var(--text-secondary); line-height:1.6;">
                    <strong>Format:</strong> PDF atau Word<br>
                    <strong>Max Size:</strong> 5MB<br>
                    <strong>Tips:</strong> Pastikan CV kamu berisi informasi yang lengkap tentang pengalaman, skill, dan pendidikan.
                </p>
            </div>""",
            unsafe_allow_html=True,
        )

    # Show CV preview if uploaded
    if st.session_state.cv_uploaded:
        st.markdown("---")
        st.markdown("### 📋 Preview CV")

        info = st.session_state.cv_file_info
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.markdown(
                f"""<div class="stat-card">
                    <div class="stat-number">{info.get('format', 'N/A')}</div>
                    <div class="stat-label">Format</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                f"""<div class="stat-card">
                    <div class="stat-number">{info.get('size_mb', 0)}</div>
                    <div class="stat-label">MB</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with col_c:
            pages = info.get("pages", info.get("paragraphs", "—"))
            label = "Halaman" if "pages" in info else "Paragraf"
            st.markdown(
                f"""<div class="stat-card">
                    <div class="stat-number">{pages}</div>
                    <div class="stat-label">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with col_d:
            score = st.session_state.get("ats_score", "N/A")
            color_style = ""
            if str(score).isdigit():
                if int(score) >= 70:
                    color_style = "color: var(--accent-emerald);"
                elif int(score) >= 50:
                    color_style = "color: var(--accent-orange);"
                else:
                    color_style = "color: var(--accent-rose);"
            
            st.markdown(
                f"""<div class="stat-card">
                    <div class="stat-number" style="{color_style} font-weight: bold;">{score}</div>
                    <div class="stat-label">ATS Score</div>
                </div>""",
                unsafe_allow_html=True,
            )

        with st.expander("📄 Lihat Isi CV (Text)", expanded=False):
            st.text_area(
                "CV Content",
                st.session_state.cv_text,
                height=300,
                disabled=True,
                label_visibility="collapsed",
            )

        # Next button
        st.markdown("<br>", unsafe_allow_html=True)
        col_l, col_r = st.columns([3, 1])
        with col_r:
            if st.button("Lihat Rekomendasi Kerja →", type="primary", use_container_width=True):
                next_step()
                st.rerun()
