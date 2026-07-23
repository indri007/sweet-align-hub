"""
Step B — Lowongan Kerja (job recommendations).

Extracted verbatim from app.py during modularization (Tahap 3).
No behavior change from the original inline block.
"""

import urllib.parse

import streamlit as st

import config
from nav import next_step, prev_step
from ui_components import render_job_card


def render_step_b():
    st.markdown(
        """<div class="hero-container animate-fade-in">
            <div class="hero-title">💼 Rekomendasi Lowongan Kerja</div>
            <div class="hero-subtitle">
                AI mencocokkan CV kamu dengan database lowongan pekerjaan di Indonesia
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["🔍 Dari Dataset (AI Match)", "🌐 Cari di Internet", "⚡ Scrape Lowongan Live"])

    search_keyword = ""

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
                        f"🎤 Mock Interview untuk posisi ini",
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

    # ── Tab 3: Live Scrape ──
    with tab3:
        st.markdown(
            """<div class="glass-card">
                <h4 style="color:var(--accent-blue);">⚡ Scrape Lowongan Live</h4>
                <p style="font-size:0.9rem; color:var(--text-secondary);">
                    Gunakan Selenium dan BeautifulSoup untuk men-scrape lowongan baru secara dinamis berdasarkan posisi target Anda. Lowongan hasil scrape akan otomatis dimasukkan ke database dan diindeks secara semantik.
                </p>
            </div>""",
            unsafe_allow_html=True,
        )

        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            scrape_keyword = st.text_input(
                "🔍 Kata Kunci Pekerjaan yang Dicari:",
                value=search_keyword or "Software Engineer",
                key="scrape_keyword_input"
            )
        with col_s2:
            scrape_limit = st.number_input("Jumlah Lowongan:", min_value=1, max_value=20, value=5)

        if st.button("🚀 Mulai Scrape Lowongan", type="primary", use_container_width=True):
            status_box = st.empty()
            progress_bar = st.progress(0)

            def update_status(text):
                status_box.info(f"⏳ {text}")

            try:
                from scraper import scrape_jobs
                update_status("Menghubungi web crawler...")
                jobs = scrape_jobs(scrape_keyword, limit=scrape_limit, status_callback=update_status)

                progress_bar.progress(100)
                status_box.success(f"✅ Sukses men-scrape dan menyimpan {len(jobs)} lowongan baru!")

                # Force reload matches
                st.session_state.job_matches = []
                st.rerun()
            except Exception as e:
                status_box.error(f"❌ Scraping gagal: {e}")

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
