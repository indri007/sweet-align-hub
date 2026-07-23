"""
JobMatch AI — Main Streamlit Application
AI-powered CV Review & Job Recommendation App

Wizard-style UI with 5 sequential steps:
A. Input CV → B. Lowongan Kerja → C. Review CV → D. Konsultasi Karir → E. Mock Interview
"""

import hashlib
import streamlit as st
import urllib.parse
from pathlib import Path

import config
from cv_processor import extract_cv_text, get_file_info, validate_cv_file

# ─── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="JobMatch AI — CV Review & Job Recommendations",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Load CSS ─────────────────────────────────────────────
css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ─── Session State Initialization ─────────────────────────
STEPS = [
    {"key": "A", "label": "Input CV", "icon": "📄", "emoji": "📄"},
    {"key": "B", "label": "Lowongan Kerja", "icon": "💼", "emoji": "💼"},
    {"key": "C", "label": "Review CV", "icon": "✍️", "emoji": "✍️"},
    {"key": "D", "label": "Konsultasi Karir", "icon": "💬", "emoji": "💬"},
    {"key": "E", "label": "Mock Interview", "icon": "🎤", "emoji": "🎤"},
]

defaults = {
    "current_step": 0,
    "cv_uploaded": False,
    "cv_text": "",
    "cv_filename": "",
    "cv_file_info": {},
    "cv_bytes": None,
    "cv_file_hash": None,
    "job_matches": [],
    "ai_summary": None,
    "cv_feedback": None,
    "ats_cv_text": None,
    "career_chat_history": [],
    "interview_history": [],
    "interview_job": None,
    "interview_started": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ─── Helper Functions ─────────────────────────────────────
def go_to_step(step_idx: int):
    """Navigate to a specific step."""
    if step_idx == 0 or st.session_state.cv_uploaded:
        st.session_state.current_step = step_idx


def next_step():
    """Go to the next step."""
    if st.session_state.current_step < len(STEPS) - 1:
        go_to_step(st.session_state.current_step + 1)


def prev_step():
    """Go to the previous step."""
    if st.session_state.current_step > 0:
        go_to_step(st.session_state.current_step - 1)


def render_match_badge(score: float) -> str:
    """Generate HTML for a match score badge."""
    if score >= 70:
        cls = "high"
    elif score >= 50:
        cls = "medium"
    else:
        cls = "low"
    return f'<span class="match-badge {cls}">🎯 {score}% Match</span>'


def render_job_card(job: dict, show_score: bool = True) -> str:
    """Generate HTML for a job listing card."""
    meta = job.get("metadata", job)
    title = meta.get("job_title", "Unknown Position")
    company = meta.get("company_name", "Unknown Company")
    location = meta.get("location", "N/A")
    work_type = meta.get("work_type", "N/A")
    salary = meta.get("salary", meta.get("salary_raw", "Tidak disebutkan"))
    if salary == "None" or not salary:
        salary = "Tidak disebutkan"
    score = job.get("similarity_score", 0)

    score_html = ""
    if show_score and score > 0:
        score_html = render_match_badge(score)

    return f"""
    <div class="job-card">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <div class="job-title">{title}</div>
                <div class="job-company">🏢 {company}</div>
            </div>
            {score_html}
        </div>
        <div class="job-meta">
            <span class="job-tag location">📍 {location}</span>
            <span class="job-tag work-type">💼 {work_type}</span>
            <span class="job-tag salary">💰 {salary}</span>
        </div>
    </div>
    """


# ─── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🎯 JobMatch AI")
    st.markdown("---")

    # Step navigation
    for i, step in enumerate(STEPS):
        is_active = i == st.session_state.current_step
        is_completed = (i == 0 and st.session_state.cv_uploaded) or (
            i < st.session_state.current_step and st.session_state.cv_uploaded
        )
        is_locked = i > 0 and not st.session_state.cv_uploaded

        # Determine visual state
        if is_active:
            icon_class = "active"
            item_class = "active"
            label_class = ""
        elif is_completed:
            icon_class = "completed"
            item_class = "completed"
            label_class = ""
        elif is_locked:
            icon_class = "locked"
            item_class = "locked"
            label_class = "locked"
        else:
            icon_class = "locked"
            item_class = ""
            label_class = ""

        # Render step item
        icon_content = "✓" if is_completed and not is_active else step["key"]

        st.markdown(
            f"""<div class="step-item {item_class}">
                <div class="step-icon {icon_class}">{icon_content}</div>
                <div class="step-label {label_class}">{step['emoji']} {step['label']}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Make clickable via button (hidden in a column trick)
        if not is_locked:
            if st.button(
                f"Go to {step['label']}",
                key=f"nav_{i}",
                use_container_width=True,
                type="secondary" if not is_active else "primary",
            ):
                go_to_step(i)
                st.rerun()

    # Progress bar
    st.markdown("---")
    progress = (st.session_state.current_step + 1) / len(STEPS)
    progress_pct = int(progress * 100)
    st.markdown(
        f"""<div style="text-align:center; margin-bottom:8px;">
            <span style="color:var(--text-secondary); font-size:0.82rem;">
                📊 Progress: Step {st.session_state.current_step + 1}/{len(STEPS)}
            </span>
        </div>
        <div class="progress-container">
            <div class="progress-fill" style="width:{progress_pct}%"></div>
        </div>""",
        unsafe_allow_html=True,
    )

    # API Status
    st.markdown("---")
    if config.is_llm_configured():
        provider_label = "Gemini" if config.LLM_PROVIDER == "gemini" else "OpenAI"
        st.success(f"✅ {provider_label} API Connected", icon="🔑")
    else:
        st.warning("⚠️ LLM API key belum diatur", icon="🔑")
        st.caption("Tambahkan di file `.env`")


# ═══════════════════════════════════════════════════════════
# STEP A: INPUT CV
# ═══════════════════════════════════════════════════════════
if st.session_state.current_step == 0:
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
            type=["pdf", "docx"],
            help="Format yang didukung: PDF, DOCX. Maksimum 100MB.",
            key="cv_uploader",
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            file_hash = hashlib.md5(file_bytes).hexdigest()
            is_new_file = file_hash != st.session_state.get("cv_file_hash")

            if not is_new_file:
                # Same file as already processed (e.g. rerun triggered by other
                # widgets) — nothing to do, avoid re-extracting/re-analyzing.
                st.success("✅ CV berhasil di-upload dan dibaca!")
            else:
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

                            # This is a different CV than before — reset every
                            # downstream result so old recommendations/review/chat
                            # don't linger and get mixed up with the new CV.
                            had_previous_cv = st.session_state.cv_uploaded
                            st.session_state.job_matches = []
                            st.session_state.ai_summary = None
                            st.session_state.cv_feedback = None
                            st.session_state.ats_cv_text = None
                            st.session_state.career_chat_history = []
                            st.session_state.interview_history = []
                            st.session_state.interview_job = None
                            st.session_state.interview_started = False

                            # Save to session state
                            st.session_state.cv_uploaded = True
                            st.session_state.cv_text = cv_text
                            st.session_state.cv_filename = uploaded_file.name
                            st.session_state.cv_file_info = file_info
                            st.session_state.cv_bytes = file_bytes
                            st.session_state.cv_file_hash = file_hash

                            if had_previous_cv:
                                st.success(
                                    "✅ CV baru berhasil di-upload! Hasil rekomendasi, review, "
                                    "chat karir, dan interview sebelumnya sudah direset."
                                )
                            else:
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


# ═══════════════════════════════════════════════════════════
# STEP B: LOWONGAN KERJA
# ═══════════════════════════════════════════════════════════
elif st.session_state.current_step == 1:
    st.markdown(
        """<div class="hero-container animate-fade-in">
            <div class="hero-title">💼 Rekomendasi Lowongan Kerja</div>
            <div class="hero-subtitle">
                AI mencocokkan CV kamu dengan database lowongan pekerjaan di Indonesia
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["🔍 Dari Dataset (AI Match)", "🌐 Cari di Internet"])

    # ── Tab 1: From Dataset (RAG) ──
    with tab1:
        # Run matching if not done yet
        if not st.session_state.job_matches:
            with st.spinner("🤖 AI sedang mencocokkan CV kamu dengan lowongan..."):
                try:
                    from agents.rag_agent import match_cv_to_jobs
                    result = match_cv_to_jobs(st.session_state.cv_text, top_k=config.TOP_K_RESULTS)
                    st.session_state.job_matches = result.get("matches", [])
                    st.session_state.ai_summary = result.get("ai_summary")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("💡 Pastikan `data_preparation.py` sudah dijalankan untuk menyiapkan data.")

        # Show AI summary if available
        if st.session_state.ai_summary:
            with st.expander("🤖 Analisis AI", expanded=True):
                st.markdown(st.session_state.ai_summary)

        # Show job matches
        if st.session_state.job_matches:
            st.markdown(f"### 🎯 Ditemukan {len(st.session_state.job_matches)} Lowongan yang Cocok")

            # Filters
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                min_score = st.slider("Minimum Match Score", 0, 100, 0, step=5)
            with col_f2:
                sort_order = st.selectbox("Urutkan", ["Tertinggi", "Terendah"])

            filtered = [j for j in st.session_state.job_matches if j.get("similarity_score", 0) >= min_score]
            filtered.sort(
                key=lambda x: x.get("similarity_score", 0),
                reverse=(sort_order == "Tertinggi"),
            )

            for job in filtered:
                st.markdown(render_job_card(job), unsafe_allow_html=True)

                meta = job.get("metadata", {})
                with st.expander(f"📋 Detail — {meta.get('job_title', 'N/A')}"):
                    st.markdown(job.get("document", "No description available."))

                    if st.button(
                        "🎤 Mock Interview untuk posisi ini",
                        key=f"interview_{job.get('id', '')}",
                    ):
                        st.session_state.interview_job = {
                            "job_title": meta.get("job_title", ""),
                            "company_name": meta.get("company_name", ""),
                            "job_description": job.get("document", ""),
                        }
                        st.session_state.current_step = 4  # Go to Mock Interview
                        st.rerun()
        else:
            if st.session_state.cv_uploaded:
                st.info("🔍 Belum ada hasil. Coba klik tombol di bawah untuk mencari ulang.")
                if st.button("🔄 Cari Ulang"):
                    st.session_state.job_matches = []
                    st.rerun()

    # ── Tab 2: External Job Search ──
    with tab2:
        st.markdown(
            """<div class="glass-card">
                <h4 style="color:var(--accent-blue);">🌐 Cari Lowongan di Internet</h4>
                <p style="font-size:0.9rem; color:var(--text-secondary);">
                    Berdasarkan CV kamu, kami telah menyiapkan link pencarian ke platform lowongan kerja populer.
                </p>
            </div>""",
            unsafe_allow_html=True,
        )

        # Extract keywords from CV for search
        cv_short = st.session_state.cv_text[:500] if st.session_state.cv_text else ""
        # Use job title from top match or generic
        if st.session_state.job_matches:
            search_keyword = st.session_state.job_matches[0].get("metadata", {}).get("job_title", "")
        else:
            search_keyword = ""

        custom_keyword = st.text_input(
            "🔑 Keyword Pencarian (edit sesuai keinginan):",
            value=search_keyword,
            placeholder="contoh: Data Analyst, Software Engineer",
        )

        if custom_keyword:
            encoded = urllib.parse.quote(custom_keyword)

            st.markdown("### 🔗 Link Pencarian")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(
                    f"""<div class="glass-card" style="text-align:center;">
                        <h3>LinkedIn</h3>
                        <p style="font-size:3rem;">💼</p>
                        <a href="https://www.linkedin.com/jobs/search/?keywords={encoded}&location=Indonesia" 
                           target="_blank" 
                           style="color:var(--accent-blue); text-decoration:none; font-weight:600;">
                            Cari di LinkedIn →
                        </a>
                    </div>""",
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    f"""<div class="glass-card" style="text-align:center;">
                        <h3>JobStreet</h3>
                        <p style="font-size:3rem;">🏢</p>
                        <a href="https://www.jobstreet.co.id/id/job-search/{encoded}-jobs/" 
                           target="_blank"
                           style="color:var(--accent-emerald); text-decoration:none; font-weight:600;">
                            Cari di JobStreet →
                        </a>
                    </div>""",
                    unsafe_allow_html=True,
                )

            with col3:
                st.markdown(
                    f"""<div class="glass-card" style="text-align:center;">
                        <h3>Google Jobs</h3>
                        <p style="font-size:3rem;">🔍</p>
                        <a href="https://www.google.com/search?q={encoded}+jobs+Indonesia&ibp=htl;jobs" 
                           target="_blank"
                           style="color:var(--accent-amber); text-decoration:none; font-weight:600;">
                            Cari di Google →
                        </a>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # Navigation buttons
    st.markdown("---")
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_l:
        if st.button("← Kembali", use_container_width=True):
            prev_step()
            st.rerun()
    with col_r:
        if st.button("Review CV →", type="primary", use_container_width=True):
            next_step()
            st.rerun()


# ═══════════════════════════════════════════════════════════
# STEP C: REVIEW CV
# ═══════════════════════════════════════════════════════════
elif st.session_state.current_step == 2:
    st.markdown(
        """<div class="hero-container animate-fade-in">
            <div class="hero-title">✍️ Review & Saran CV</div>
            <div class="hero-subtitle">
                AI akan menganalisis CV kamu dan memberikan feedback untuk meningkatkan kualitasnya
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    if not config.is_llm_configured():
        st.warning(
            "⚠️ Fitur ini membutuhkan LLM API key. Tambahkan `GEMINI_API_KEY` (atau `OPENAI_API_KEY`) di file `.env`",
            icon="🔑",
        )
    else:
        tab1, tab2 = st.tabs(["📊 Feedback & Saran", "📝 Generate CV ATS"])

        # ── Tab 1: CV Feedback ──
        with tab1:
            if st.session_state.cv_feedback is None:
                if st.button("🤖 Analisis CV Saya", type="primary", use_container_width=True):
                    with st.spinner("🤖 AI sedang menganalisis CV kamu..."):
                        from agents.cv_analyzer_agent import review_cv
                        result = review_cv(st.session_state.cv_text)
                        if result["available"] and result["feedback"]:
                            st.session_state.cv_feedback = result["feedback"]
                            st.rerun()
                        else:
                            st.error("❌ Gagal menganalisis CV.")
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
                if st.button("✨ Generate CV ATS", type="primary", use_container_width=True):
                    with st.spinner("✨ AI sedang membuat CV ATS-friendly..."):
                        from agents.cv_analyzer_agent import generate_ats_cv
                        result = generate_ats_cv(st.session_state.cv_text)
                        if result["available"] and result["ats_text"]:
                            st.session_state.ats_cv_text = result["ats_text"]
                            st.rerun()
                        else:
                            st.error("❌ Gagal membuat CV ATS.")
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
                        from agents.cv_analyzer_agent import export_cv_to_docx
                        docx_bytes = export_cv_to_docx(st.session_state.ats_cv_text)
                        st.download_button(
                            "📄 Download Word (.docx)",
                            data=docx_bytes,
                            file_name="CV_ATS_Optimized.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(f"Error generating DOCX: {e}")

                with col2:
                    try:
                        from agents.cv_analyzer_agent import export_cv_to_pdf
                        pdf_bytes = export_cv_to_pdf(st.session_state.ats_cv_text)
                        st.download_button(
                            "📑 Download PDF (.pdf)",
                            data=pdf_bytes,
                            file_name="CV_ATS_Optimized.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(f"Error generating PDF: {e}")

                if st.button("🔄 Generate Ulang"):
                    st.session_state.ats_cv_text = None
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


# ═══════════════════════════════════════════════════════════
# STEP D: KONSULTASI KARIR
# ═══════════════════════════════════════════════════════════
elif st.session_state.current_step == 3:
    st.markdown(
        """<div class="hero-container animate-fade-in">
            <div class="hero-title">💬 Konsultasi Karir</div>
            <div class="hero-subtitle">
                Diskusikan cita-cita dan tujuan karir kamu dengan AI Career Consultant
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    if not config.is_llm_configured():
        st.warning(
            "⚠️ Fitur ini membutuhkan LLM API key. Tambahkan `GEMINI_API_KEY` (atau `OPENAI_API_KEY`) di file `.env`",
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


# ═══════════════════════════════════════════════════════════
# STEP E: MOCK INTERVIEW
# ═══════════════════════════════════════════════════════════
elif st.session_state.current_step == 4:
    st.markdown(
        """<div class="hero-container animate-fade-in">
            <div class="hero-title">🎤 Mock Interview</div>
            <div class="hero-subtitle">
                Simulasi interview text dengan AI sebagai HR Interviewer.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    if not config.is_llm_configured():
        st.warning(
            "⚠️ Fitur ini membutuhkan LLM API key. Tambahkan `GEMINI_API_KEY` (atau `OPENAI_API_KEY`) di file `.env`",
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

            # Start interview if not started
            if not st.session_state.interview_started:
                if st.button("🎬 Mulai Interview Sekarang", type="primary"):
                    with st.spinner("🤖 HR sedang mempersiapkan interview..."):
                        from agents.interview_agent import start_interview
                        result = start_interview(st.session_state.cv_text, job)
                        if result["available"] and result["response"]:
                            st.session_state.interview_history = [
                                {"role": "assistant", "content": result["response"]}
                            ]
                            st.session_state.interview_started = True
                            st.rerun()
            else:
                # Display interview conversation
                for msg in st.session_state.interview_history:
                    if msg["role"] == "assistant":
                        st.markdown(
                            f'<div class="chat-ai">🤵 HR: {msg["content"]}</div>',
                            unsafe_allow_html=True,
                        )

                    else:
                        st.markdown(
                            f'<div class="chat-user">🧑 Kamu: {msg["content"]}</div>',
                            unsafe_allow_html=True,
                        )

                # Input area
                answer = st.chat_input("Ketik jawaban kamu...")
                if answer:
                    st.session_state.interview_history.append(
                        {"role": "user", "content": answer}
                    )
                    with st.spinner("🤵 HR sedang mengevaluasi jawaban..."):
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
                    st.rerun()

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
