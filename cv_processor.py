"""
CV Processor — Extract text from PDF, DOCX, and DOC files.
"""

import io
from pathlib import Path
import pdfplumber
from docx import Document
import config


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text content from a PDF file with OCR fallback for scanned PDFs."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    text = "\n\n".join(text_parts).strip()

    # OCR Fallback if text is empty or too short (likely scanned PDF)
    if len(text) < 50:
        # Fallback 1: Use Gemini's native multimodal capabilities to read scanned PDF directly
        if config.is_gemini_configured():
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=config.GEMINI_API_KEY)
                response = client.models.generate_content(
                    model=config.GEMINI_MODEL,
                    contents=[
                        types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                        "Ekstrak dan ketik ulang seluruh teks yang ada di dalam dokumen CV ini secara lengkap, pertahankan urutan dan bahasanya.",
                    ]
                )
                if response.text:
                    return response.text.strip()
            except Exception:
                # Log or silenty ignore to proceed to Fallback 2
                pass

        # Fallback 2: Local Tesseract OCR via pdf2image + pytesseract
        try:
            from pdf2image import convert_from_bytes
            import pytesseract
            images = convert_from_bytes(file_bytes)
            ocr_parts = []
            for image in images:
                ocr_text = pytesseract.image_to_string(image)
                if ocr_text:
                    ocr_parts.append(ocr_text)
            ocr_result = "\n\n".join(ocr_parts).strip()
            if ocr_result:
                return ocr_result
        except Exception:
            pass

    return text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text content from a DOCX file."""
    doc = Document(io.BytesIO(file_bytes))
    text_parts = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)
    # Also extract from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                text_parts.append(row_text)
    return "\n".join(text_parts)


def extract_text_from_doc(file_bytes: bytes, filename: str) -> str:
    """
    Extract text content from a legacy .doc file.
    Uses doc_reader.py (LibreOffice convert -> docx, with antiword fallback).
    Writes to a temp file first since doc_reader works on file paths, not bytes.
    """
    import tempfile
    from doc_reader import read_word_document, DocReadError

    with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        return read_word_document(tmp_path)
    except DocReadError as e:
        raise ValueError(
            f"Gagal membaca file .doc '{filename}'. "
            f"Coba simpan ulang sebagai .docx. Detail: {e}"
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def extract_cv_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from a CV file based on its extension.
    Supports PDF, DOCX, and legacy DOC formats.
    """
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext == ".docx":
        return extract_text_from_docx(file_bytes)
    elif ext == ".doc":
        return extract_text_from_doc(file_bytes, filename)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use PDF, DOCX, or DOC.")


def get_file_info(file_bytes: bytes, filename: str) -> dict:
    """Get basic file info."""
    ext = Path(filename).suffix.lower()
    size_mb = len(file_bytes) / (1024 * 1024)
    info = {
        "filename": filename,
        "format": ext.upper().replace(".", ""),
        "size_mb": round(size_mb, 2),
        "size_bytes": len(file_bytes),
    }
    # Count pages for PDF
    if ext == ".pdf":
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                info["pages"] = len(pdf.pages)
        except Exception:
            info["pages"] = "Unknown"
    elif ext == ".docx":
        try:
            doc = Document(io.BytesIO(file_bytes))
            info["paragraphs"] = len([p for p in doc.paragraphs if p.text.strip()])
        except Exception:
            info["paragraphs"] = "Unknown"
    elif ext == ".doc":
        info["note"] = "Legacy Word format (dikonversi otomatis via LibreOffice)"
    return info


def validate_cv_file(file_bytes: bytes, filename: str, max_size_mb: int = 100) -> tuple[bool, str]:
    """
    Validate CV file format and size.
    Returns (is_valid, error_message).
    """
    ext = Path(filename).suffix.lower()
    if ext not in (".pdf", ".docx", ".doc"):
        return False, f"Format {ext} tidak didukung. Gunakan PDF, DOCX, atau DOC."

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"Ukuran file {size_mb:.1f}MB melebihi batas {max_size_mb}MB."

    return True, ""
