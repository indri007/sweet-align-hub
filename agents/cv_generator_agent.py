"""
CV Generator Agent — Specializes in rewriting and generating ATS-optimized CVs
using Harvard Business School resume standards.
"""

import io
from docx import Document
from docx.shared import Pt, RGBColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import config
from llm_client import chat_completion

ATS_CV_PROMPT = """Kamu adalah CV Writer Expert profesional lulusan Harvard Business School dan spesialis optimasi ATS (Applicant Tracking System).
Tugasmu adalah menulis ulang CV pengguna menjadi format ATS yang sangat kuat, tajam, dan berdampak tinggi.

Gunakan gaya bahasa percakapan profesional, langsung pada poin utama, hindari transisi klise seperti "Tentu, ini adalah..." atau "Semoga membantu". Outputmu harus MURNI teks CV Markdown yang siap diunduh!

ATURAN WAJIB (STANDAR CV ATS-FRIENDLY):
1. **Struktur Konten yang Baku:** Gunakan format Markdown yang sangat rapi dan berurutan:
   - Kontak Informasi (Contact Information)
   - Ringkasan Profesional (Professional Summary)
   - Pengalaman Kerja (Work Experience) - Urutan Kronologis Terbalik
   - Pendidikan (Education)
   - Keahlian (Skills) - Dibagi Teknis (Hard Skills) dan Lunak (Soft Skills)
   - Sertifikasi (Certifications) - Opsional

2. **Detail Komponen:**
   - **Kontak Info:** Nama Lengkap (Heading 1), Telepon, Email Profesional, LinkedIn, Kota & Provinsi Domisili.
   - **Ringkasan Profesional:** 3-4 kalimat padat di awal CV yang merangkum pengalaman utama, keahlian spesial, dan nilai tambah terbesar.
   - **Pengalaman Kerja:** Jabatan | Perusahaan & Lokasi | Bulan Tahun - Bulan Tahun. Gunakan format poin (maks 5-6 poin per pekerjaan).
   - **Pendidikan:** Gelar & Jurusan | Nama Universitas | Tahun Lulus | IPK (cantumkan jika relevan).

3. **Action Verbs & Berbasis Metrik (Krusial):** 
   Mulai SETIAP poin pengalaman kerja dengan kata kerja tindakan aktif (misal: Mengelola, Merancang, Meningkatkan, Memimpin, Menginisiasi, Mengoptimalkan). JANGAN mulai dengan "Bertanggung jawab untuk...".
   Sertakan metrik atau angka kuantitatif untuk menunjukkan pencapaian nyata (contoh: "Meningkatkan efisiensi waktu hingga 20% melalui otomatisasi"). Jika angka asli tidak ada, perkirakan metrik yang realistis namun logis.

4. **Tanpa Fluff & Optimasi Kata Kunci (Keywords):** 
   Hapus kata-kata manis yang tidak bisa diukur. Fokus pada HARD SKILL, TOOLS, dan HASIL.
   Integrasikan kata kunci dari lowongan kerja (jika ada) secara alami tanpa *keyword stuffing*.

Format Keluaran yang Diharapkan:
# [Nama Lengkap]
[Email] | [Nomor Telepon] | [LinkedIn] | [Kota, Provinsi]

## PROFESSIONAL SUMMARY
[3-4 kalimat padat...]

## PROFESSIONAL EXPERIENCE
**[Nama Jabatan]** | [Nama Perusahaan & Lokasi]
[Bulan Tahun - Bulan Tahun]
- [Action Verb] [Konteks Tugas] yang menghasilkan [Metrik/Hasil Terukur] menggunakan [Tools/Skills].
- [Action Verb] ...

## EDUCATION
**[Gelar & Jurusan]** | [Nama Universitas]
[Tahun Lulus] | IPK: [Angka]

## SKILLS
- **Hard Skills:** [Skill 1], [Skill 2], [Skill 3]
- **Soft Skills:** [Skill 1], [Skill 2]
"""


def generate_ats_cv(cv_text: str, target_job: dict = None, language: str = "auto") -> dict:
    """
    Generate an ATS-friendly version of the CV using Harvard standards.

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
            system_prompt += f"""\n\nPENTING: Optimalkan CV ini KHUSUS untuk menembus posisi "{target_job.get('job_title', '')}" di "{target_job.get('company_name', '')}".
Sesuaikan keywords, skills, dan pengalaman yang di-highlight agar sangat relevan dengan deskripsi pekerjaan tersebut!"""

        if language == "id":
            system_prompt += "\n\nOutput CV ATS-friendly HARUS ditulis dalam Bahasa Indonesia."
        elif language == "en":
            system_prompt += "\n\nOutput CV ATS-friendly HARUS ditulis dalam Bahasa Inggris (English)."

        reply = chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"CV Asli/Data Mentah:\n\n{cv_text}{target_context}"},
            ],
            temperature=0.4,
            max_tokens=3500,
            agent_id=2,
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
    h1_style = ParagraphStyle(
        "Heading1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        spaceAfter=12,
        textColor="#1f2937",
    )
    h2_style = ParagraphStyle(
        "Heading2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        spaceAfter=8,
        spaceBefore=12,
        textColor="#374151",
    )
    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        spaceAfter=6,
        leading=14,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=normal_style,
        leftIndent=20,
        firstLineIndent=-10,
    )

    story = []
    lines = cv_text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue

        if line.startswith("# "):
            clean = line.lstrip("#").strip()
            story.append(Paragraph(clean, h1_style))
        elif line.startswith("## "):
            clean = line.lstrip("#").strip()
            story.append(Paragraph(clean, h2_style))
        elif line.upper() == line and len(line) > 3 and not line.startswith("-"):
            story.append(Paragraph(line, h2_style))
        elif line.startswith("- ") or line.startswith("• "):
            clean = line.lstrip("-•").strip()
            story.append(Paragraph(f"• {clean}", bullet_style))
        else:
            story.append(Paragraph(line, normal_style))

    doc.build(story)
    return buffer.getvalue()
