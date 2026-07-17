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
            help="Format yang didukung: PDF, DOCX. Maksimum 100MB.",
            key="cv_uploader",
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()

            # Validate size
            max_bytes = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
            if len(file_bytes) > max_bytes:
                st.error(f"❌ File terlalu besar. Maksimum {config.MAX_UPLOAD_SIZE_MB}MB.")
                st.stop()

            # Validate
            is_valid, error_msg = validate_cv_file(file_bytes, uploaded_file.name)

            if not is_valid:
                st.error(f"❌ {error_msg}")
            else:
                # Extract text
                with st.spinner("📖 Membaca CV kamu..."):
                    try:
                        cv_text = extract_cv_text(file_bytes, uploaded_file.name)
                        file_info = get_file_info(file_bytes, uploaded_file.name)

                        # Save to session state
                        st.session_state.cv_uploaded = True
                        st.session_state.cv_text = cv_text
                        st.session_state.cv_filename = uploaded_file.name
                        st.session_state.cv_file_info = file_info
                        st.session_state.cv_bytes = file_bytes

                        st.success("✅ CV berhasil di-upload dan dibaca!")

                    except Exception as e:
                        st.error(f"❌ Gagal membaca CV: {str(e)}")

    with col2:
        st.markdown(
            """<div class="glass-card">
                <h4 style="color:var(--accent-blue);">📋 Panduan</h4>
                <p style="font-size:0.85rem; color:var(--text-secondary); line-height:1.6;">
                    <strong>Format:</strong> PDF atau Word<br>
                    <strong>Max Size:</strong> 100MB<br>
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
        col_a, col_b, col_c = st.columns(3)
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
