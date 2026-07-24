"""
CV Analyzer Agent — Reviews CV content and generates feedback.
Provides ATS score, improvement suggestions, and generates ATS-friendly CV.
"""

import io
from docx import Document
from docx.shared import Pt, RGBColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import config
from llm_client import chat_completion


REVIEW_PROMPT = """You are a professional ATS (Applicant Tracking System) consultant and Senior HR Recruiter. Your task is to analyze the following CV and provide an objective assessment based on these criteria:

A. ATS Parsing (weight 35%)
   - File format & structure compatibility.
   - Keyword relevance and keyword density.
   - Standard headings usage (Work Experience, Education, Skills).
   - Date format consistency and chronology.

B. Konten/HRD (weight 60%)
   - Relevance of work experience and career progression.
   - Quantified achievements and measurable metrics.
   - Skill match and education background.
   - CV length, grammar, and absence of red flags.

C. Match Scoring (weight 5%)
   - Match between mandatory required skills (from target job) vs skills in CV.

OUTPUT INSTRUCTIONS — provide results EXACTLY in this format (use these exact headings):

## 📊 ATS & HRD Score: [score]/100

## 📋 Skor Per Kategori
- ATS Parsing: [x]/35
- Konten/HRD: [x]/60
- Match Scoring: [x]/5

## ⚠️ Area yang Perlu Diperbaiki
- [point 1]
- [point 2]
...

## 💡 Saran Perbaikan
- [saran spesifik 1]
- [saran spesifik 2]
...

## 🔑 Keywords yang Terdeteksi
[list keywords/skills yang ditemukan di CV]

## 📝 Ringkasan Profil
[ringkasan singkat profil kandidat berdasarkan CV]

Respond in Bahasa Indonesia. Focus on SPECIFIC, actionable findings only."""




def review_cv(cv_text: str, target_job: dict = None) -> dict:
    """
    Analyze CV and return structured feedback.

    Returns dict with:
    - "feedback": AI-generated feedback markdown
    - "available": whether OpenAI/N8N is configured
    """
    # Try N8N first
    if config.is_n8n_configured():
        try:
            from n8n_client import review_cv_n8n
            ai_text = review_cv_n8n(cv_text, target_job=target_job)
            if ai_text and not ai_text.startswith("Error") and not ai_text.startswith("Tidak dapat") and not ai_text.startswith("N8N"):
                return {"feedback": ai_text, "available": True}
        except Exception:
            pass

    if not config.is_llm_configured():
        return {
            "feedback": None,
            "available": False,
        }

    try:
        system_prompt = REVIEW_PROMPT
        target_context = ""
        if target_job:
            target_context = f"\n\nPosisi Target:\n- Jabatan: {target_job.get('job_title', 'N/A')}\n- Perusahaan: {target_job.get('company_name', 'N/A')}\n- Deskripsi Pekerjaan: {target_job.get('job_description', 'N/A')}"
            system_prompt += f"""\n\nIMPORTAN: User menargetkan posisi spesifik. 
Berikan feedback CV yang SPESIFIK dan TERARAH untuk posisi \"{target_job.get('job_title', '')}\". 
Analisis apakah CV user sudah cocok untuk posisi tersebut, identifikasi gap yang perlu diperbaiki, dan berikan saran konkret agar CV lebih menarik untuk posisi ini."""

        reply = chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Berikut adalah CV yang perlu di-review:\n\n{cv_text}{target_context}"},
            ],
            temperature=0.5,
            max_tokens=2500,
            agent_id=1,
        )
        return {
            "feedback": reply,
            "available": True,
        }
    except Exception as e:
        return {
            "feedback": f"Error: {str(e)}",
            "available": True,
        }


