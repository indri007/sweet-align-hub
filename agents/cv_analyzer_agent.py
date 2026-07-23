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


ATS_CV_PROMPT = """Kamu adalah CV Writer Expert profesional dan spesialis optimasi ATS (Applicant Tracking System).
Tugasmu adalah mengubah CV asli user menjadi CV profesional yang sangat ATS-friendly, rapi, terstruktur, dan memiliki daya jual tinggi bagi HRD.

Ikuti petunjuk struktur dan pemformatan berikut dengan sangat ketat:

### 1. FORMAT & STRUKTUR CV
Gunakan susunan bagian/section berikut secara berurutan dengan heading bertanda `## `:

## [NAMA LENGKAP KANDIDAT]
[Email] | [Nomor Telepon] | [Kota/Kabupaten, Provinsi] | [Link LinkedIn]

## RINGKASAN PROFIL
Tulis ringkasan profesional singkat (3-4 kalimat) yang merangkum keahlian utama, pengalaman relevan, nilai jual unik kandidat, dan apa yang ingin mereka capai secara profesional. Buat agar sangat menarik bagi perekrut.

## PENGALAMAN KERJA
Format setiap riwayat pekerjaan secara konsisten sebagai berikut:
**[Nama Jabatan/Posisi]** | [Nama Perusahaan] | [Bulan Tahun Mulai] – [Bulan Tahun Selesai/Sekarang]
- Gunakan poin-poin bullet (`- `).
- Setiap poin harus dimulai dengan Kata Kerja Aksi yang kuat (Action Verbs), contoh: *Merancang, Mengimplementasikan, Memimpin, Meningkatkan, Mengoptimalkan, Menganalisis*.
- Gunakan formula XYZ untuk menulis pencapaian: "Berhasil mencapai [X], diukur dengan [Y], dengan melakukan [Z]". Usahakan memasukkan angka/metrik konkret (misal: persentase kenaikan, efisiensi waktu, jumlah user) untuk memberikan dampak visual yang kuat.

## PENDIDIKAN
Format setiap riwayat pendidikan secara konsisten sebagai berikut:
**[Nama Gelar/Jurusan]** | [Nama Universitas/Sekolah] | [Tahun Kelulusan]
- Tambahkan info relevan jika ada (misal: IPK jika di atas 3.0/4.0, atau pencapaian akademis penting).

## KEAHLIAN (SKILLS)
Kelompokkan keahlian ke dalam kategori agar mudah dibaca oleh ATS dan HRD, contoh:
- **Keahlian Teknis (Hard Skills)**: [Daftar keahlian teknis utama]
- **Alat & Teknologi (Tools)**: [Software/Tools/Bahasa Pemrograman yang dikuasai]
- **Keahlian Interpersonal (Soft Skills)**: [Daftar soft skills yang relevan]

## SERTIFIKASI & PROJEK (Opsional)
Jika ada sertifikasi atau projek penting di CV asli, format sebagai berikut:
**[Nama Sertifikasi/Projek]** | [Penerbit/Penyelenggara/Tahun]

### 2. ATURAN PENULISAN (RULES)
1. JANGAN gunakan emoji dekoratif di dalam konten CV karena dapat membingungkan sistem parse ATS.
2. Gunakan tata bahasa profesional (Bahasa Indonesia baku atau Bahasa Inggris profesional, sesuaikan dengan bahasa utama pada CV asli).
3. HANYA keluarkan teks CV hasil optimasi saja dari baris pertama hingga terakhir. JANGAN berikan kalimat pembuka ("Berikut adalah...", "Tentu, ini CV...", dll.) atau kalimat penutup."""


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


def generate_ats_cv(cv_text: str, target_job: dict = None, language: str = "auto") -> dict:
    """
    Generate an ATS-friendly version of the CV.

    Returns dict with:
    - "ats_text": improved CV content as plain text
    - "available": whether OpenAI/N8N is configured
    """
    # Try N8N first
    if config.is_n8n_configured():
        try:
            from n8n_client import generate_ats_cv_n8n
            ai_text = generate_ats_cv_n8n(cv_text, target_job=target_job)
            if ai_text and not ai_text.startswith("Error") and not ai_text.startswith("Tidak dapat") and not ai_text.startswith("N8N"):
                return {"ats_text": ai_text, "available": True}
        except Exception:
            pass

    if not config.is_llm_configured():
        return {"ats_text": None, "available": False}

    try:
        system_prompt = ATS_CV_PROMPT
        target_context = ""
        if target_job:
            target_context = f"\n\nPosisi Target:\n- Jabatan: {target_job.get('job_title', 'N/A')}\n- Perusahaan: {target_job.get('company_name', 'N/A')}\n- Deskripsi Pekerjaan: {target_job.get('job_description', 'N/A')}"
            system_prompt += f"""\n\nIMPORTAN: Optimalkan CV ini KHUSUS untuk posisi \"{target_job.get('job_title', '')}\" di \"{target_job.get('company_name', '')}\".
Sesuaikan keywords, skills, dan pengalaman yang di-highlight agar relevan dengan posisi tersebut."""

        if language == "id":
            system_prompt += "\n\nOutput CV ATS-friendly HARUS ditulis dalam Bahasa Indonesia."
        elif language == "en":
            system_prompt += "\n\nOutput CV ATS-friendly HARUS ditulis dalam Bahasa Inggris (English)."

        reply = chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"CV Asli:\n\n{cv_text}{target_context}"},
            ],
            temperature=0.4,
            max_tokens=3000,
        )
        return {
            "ats_text": reply,
            "available": True,
        }
    except Exception as e:
        return {"ats_text": f"Error: {str(e)}", "available": True}


def export_cv_to_docx(cv_text: str) -> bytes:
    """Export CV text to a formatted DOCX file. Returns bytes."""
    doc = Document()

    # Set default font
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)
    font.color.rgb = RGBColor(33, 33, 33)

    # Parse and add content
    lines = cv_text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            doc.add_paragraph("")
            continue

        # Detect headings (lines in ALL CAPS or starting with ##)
        if line.startswith("## ") or line.startswith("# "):
            clean = line.lstrip("#").strip()
            p = doc.add_heading(clean, level=2)
        elif line.upper() == line and len(line) > 3 and not line.startswith("-"):
            p = doc.add_heading(line, level=2)
        elif line.startswith("- ") or line.startswith("• "):
            clean = line.lstrip("-•").strip()
            p = doc.add_paragraph(clean, style="List Bullet")
        else:
            p = doc.add_paragraph(line)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def export_cv_to_pdf(cv_text: str) -> bytes:
    """Export CV text to a formatted PDF file. Returns bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    heading_style = ParagraphStyle(
        "CVHeading",
        parent=styles["Heading2"],
        fontSize=13,
        spaceAfter=6,
        spaceBefore=14,
        textColor="#1a1a2e",
    )
    body_style = ParagraphStyle(
        "CVBody",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=4,
        leading=14,
    )
    bullet_style = ParagraphStyle(
        "CVBullet",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=3,
        leftIndent=20,
        leading=14,
        bulletIndent=10,
    )

    elements = []
    lines = cv_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            elements.append(Spacer(1, 6))
            continue

        # Escape XML special characters for reportlab
        safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        if line.startswith("## ") or line.startswith("# "):
            clean = safe_line.lstrip("#").strip()
            elements.append(Paragraph(clean, heading_style))
        elif line.upper() == line and len(line) > 3 and not line.startswith("-"):
            elements.append(Paragraph(safe_line, heading_style))
        elif line.startswith("- ") or line.startswith("• "):
            clean = safe_line.lstrip("-•").strip()
            elements.append(Paragraph(f"• {clean}", bullet_style))
        else:
            elements.append(Paragraph(safe_line, body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
