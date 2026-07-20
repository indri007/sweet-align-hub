"""
UI Components — reusable HTML/markdown rendering helpers.

Extracted from app.py during modularization (Tahap 3 — Struktur Kode).
No behavior change: these are the exact same functions that previously
lived at the top level of app.py.
"""


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
