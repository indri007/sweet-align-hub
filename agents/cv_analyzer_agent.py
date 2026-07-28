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
from database import DatabaseManager
from sqlalchemy import text as sql_text


REVIEW_PROMPT_TEMPLATE = """You are a professional ATS (Applicant Tracking System) consultant and Senior HR Recruiter with 15+ years experience screening thousands of CVs. Your task is to analyze the following CV and provide an objective, STRICT assessment based on these criteria:

{rubric_context}

SCORING RULES (WAJIB DIIKUTI):
- Kuantifikasi & Metrik: Berikan PENALTI BESAR (-15 poin dari skor keseluruhan) jika CV tidak memuat angka/metrik kuantitatif apapun pada bagian Pengalaman Kerja. Poin pengalaman seperti "Bertanggung jawab atas X" atau "Membantu tim dalam Y" TANPA angka dampak dianggap LEMAH dan harus dicatat secara eksplisit di bagian Area yang Perlu Diperbaiki.
- Jadilah TEGAS dan JUJUR. Jangan berikan nilai tinggi untuk CV yang generik, penuh kata-kata klise, atau minim bukti konkret.
- Sertakan contoh kalimat konkret yang perlu diperbaiki (kutip langsung dari CV) di bagian Saran Perbaikan.

OUTPUT INSTRUCTIONS — provide results EXACTLY in this format (use these exact headings):

## 📊 ATS & HRD Score: [score]/100

## 📋 Skor Per Kategori
Tuliskan nama setiap kategori dari kriteria di atas, lalu berikan skor pencapaian kandidat dibandingkan total bobot kategori tersebut (Contoh: - ATS Parsing: 25/35).

## ⚠️ Area yang Perlu Diperbaiki
- [point 1 — sertakan kutipan dari CV jika relevan]
- [point 2]
...

## 💡 Saran Perbaikan (Spesifik & Actionable)
- [saran spesifik 1 — berikan contoh kalimat yang lebih baik jika memungkinkan]
- [saran spesifik 2]
...

## 🔑 Keywords yang Terdeteksi
[list keywords/skills yang ditemukan di CV]

## 📝 Ringkasan Profil
[ringkasan singkat profil kandidat berdasarkan CV]

Respond in Bahasa Indonesia. Be SPECIFIC, CRITICAL, and ACTIONABLE. Avoid vague praise."""

def get_scoring_rubric_context() -> str:
    """Fetch scoring rubric from database to inject into prompt."""
    try:
        db = DatabaseManager()
        with db.engine.connect() as conn:
            result = conn.execute(sql_text("SELECT kategori, kriteria, bobot_persen FROM scoring_rubric"))
            rows = result.fetchall()
            if not rows:
                return "Gunakan kriteria ATS standar (ATS Parsing, Konten, dsb)."
            
            categories = {}
            for row in rows:
                cat = row[0]
                crit = row[1]
                weight = row[2]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append((crit, weight))
            
            rubric_text = ""
            for cat, items in categories.items():
                total_weight = sum(w for c, w in items)
                rubric_text += f"{cat} (total bobot: {total_weight}%)\n"
                for crit, weight in items:
                    rubric_text += f"   - {crit} (bobot: {weight}%)\n"
                rubric_text += "\n"
            return rubric_text.strip()
    except Exception as e:
        print(f"Warning: Failed to fetch scoring rubric: {e}")
    return "Gunakan kriteria ATS standar (ATS Parsing, Konten, dsb)."
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
        rubric_context = get_scoring_rubric_context()
        system_prompt = REVIEW_PROMPT_TEMPLATE.replace("{rubric_context}", rubric_context)
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


