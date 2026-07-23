import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Konten patch
# ---------------------------------------------------------------------------

NEW_SECTION_6 = """## 6. Fitur CV Analysis — Aiven Caching (Rencana)

Hasil AI disimpan permanen ke tabel `cv_analysis_results` di Aiven:

| Kolom | Isi |
|---|---|
| `cv_content_hash` | **[FIX]** SHA-256 dari teks CV ter-parse — kunci cache utama. Tanpa ini, re-upload CV yang sudah diperbarui untuk posisi yang sama akan salah mengembalikan hasil analisis versi lama. |
| `email` | Identitas user |
| `language` | `id` / `en` (simpan versi terpisah, tidak saling timpa) |
| `job_title`, `job_description` | Loker target |
| `hr_knowledge_context` | Referensi HRD dari Qdrant yang dipakai AI |
| `ats_score` | Skor ATS hasil analisis |
| `cv_feedback` | Kelebihan, kekurangan, saran |
| `ats_cv_text` | Teks CV versi ATS-friendly |
| `created_at` | Timestamp |

**Unique key**: `(cv_content_hash, job_id, language)` — bukan `(email, job_title, job_description)`.
Alasan: dua field terakhir bisa berubah redaksinya (typo job_title, deskripsi loker
diedit) tanpa isi CV berubah, dan sebaliknya isi CV bisa berubah tanpa job_title
berubah. Hash konten CV adalah satu-satunya sinyal yang benar-benar menandakan
"perlu dianalisis ulang atau tidak".

**Alur runtime (diperbaiki):**
1. Hitung `cv_content_hash = sha256(parsed_cv_text)`.
2. Cek Aiven dengan `(cv_content_hash, job_id, language)` → jika ada → tampilkan langsung (**0 token**).
3. Jika belum ada → panggil LLM → simpan ke Aiven dengan hash tersebut → tampilkan.

```python
import hashlib

def get_or_analyze_cv(parsed_cv_text: str, job_id: str, language: str):
    cv_content_hash = hashlib.sha256(parsed_cv_text.encode("utf-8")).hexdigest()
    cached = query_cv_analysis_results(cv_content_hash, job_id, language)
    if cached:
        return cached  # 0 token
    result = call_llm_for_cv_analysis(parsed_cv_text, job_id, language)
    save_cv_analysis_results(cv_content_hash, job_id, language, result)
    return result
```
"""

OPEN_DECISIONS_SECTION = """## 11. Konflik Arsitektur & Keputusan Terbuka

Ditemukan lewat perbandingan silang antara dokumen ini, `PRD_JobMatch_AI_v2`
(disusun bersama Claude), dan `Dokumentasi_Scope_Batasan_Pengujian_Chatbot_CS_HRD.md`
(dokumen scope resmi). Belum diputuskan sepihak — perlu keputusan produk sebelum
dokumen ini dianggap sumber kebenaran tunggal.

| # | Topik | Dokumen ini bilang | Scope resmi / PRD v2 bilang | Perlu diputuskan |
|---|---|---|---|---|
| 1 | Voice (TTS/STT) | gTTS + Whisper STT sudah diimplementasikan, ada di checklist validasi | Eksplisit **out-of-scope**: "sistem murni berbasis teks" (Dok. Scope §3.4) | Cabut fitur voice, atau revisi scope resmi untuk memasukkannya |
| 2 | Status N8N | `USE_N8N=false` default, arsitektur live Python langsung ke Groq/Gemini/Qdrant/Aiven | n8n sebagai orkestrator **wajib** (Dok. Scope §2.4); seluruh strategi pengujian integrasi mengetes webhook n8n | Migrasikan ke n8n, atau revisi scope resmi jadi opsional |
| 3 | LLM provider | Groq (llama-3.3-70b) utama, Gemini Flash fallback | Gemini Chat Model sebagai satu-satunya LLM (JobMatch AI V3.json) | Pilih satu provider resmi, dokumentasikan rate-limit/cost masing-masing |
| 4 | Nama collection Qdrant untuk lowongan | `indonesian_jobs_gemini` (473 vektor) | `indonesian_jobs_n8n` | Cek Qdrant dashboard: satu collection yang di-rename, atau dua collection duplikat (boros storage + risiko out-of-sync) |
| 5 | Jumlah soal interview | "41 pertanyaan, 10 kompetensi STAR" | 40 soal (10 kompetensi × 4 tahap STAR) di `Interview_Questions.json` yang ter-upsert | Cek `Interview_Questions.xlsx` sumber: ada 1 soal ekstra yang belum ter-cover `build_interview_kb.py`? |

**Catatan:** baris "Dampak Efisiensi Token" pada Bagian 5 dokumen ini sebelumnya
mengklaim angka penghematan token spesifik tanpa sumber/benchmark. Klaim tersebut
telah diganti dengan pernyataan kualitatif sampai ada pengukuran token
before/after yang nyata untuk didokumentasikan di sini.
"""

TOKEN_CLAIM_PATTERN = re.compile(
    r"Pendekatan ini secara signifikan.*?mengurangi risiko terkena \*rate-limit\*\.",
    re.DOTALL,
)
TOKEN_CLAIM_REPLACEMENT = (
    "Pendekatan ini mengurangi panggilan LLM untuk generate soal, karena diambil "
    "langsung dari Qdrant. LLM hanya dipanggil untuk tugas penalaran tingkat "
    "tinggi (evaluasi jawaban kandidat). *(Catatan: klaim angka penghematan token "
    "spesifik sebelumnya dihapus karena tidak ada benchmark yang mendukungnya — "
    "lihat Bagian 11.)*"
)

ERD_NEW_ENTITY_BLOCK = """  USERS ||--o{ CV_ANALYSIS_RESULTS : requests
  JOBS ||--o{ CV_ANALYSIS_RESULTS : analyzed_against
"""

ERD_NEW_ENTITY_DEF = """  CV_ANALYSIS_RESULTS {
    string cv_content_hash PK "SHA-256 dari teks CV ter-parse"
    string user_id FK
    string job_id FK
    string language
    text hr_knowledge_context
    float ats_score
    text cv_feedback
    text ats_cv_text
    datetime created_at
  }
"""


# ---------------------------------------------------------------------------
# Patch functions
# ---------------------------------------------------------------------------

def patch_prd(text: str) -> tuple[str, list[str]]:
    changes = []

    # 1. Ganti section 6 (dari "## 6." sampai sebelum "## 7." atau "## 10." dst)
    if "cv_content_hash" in text:
        changes.append("PRD: skema cv_analysis_results sudah punya cv_content_hash — dilewati.")
    else:
        section_pattern = re.compile(
            r"## 6\. Fitur CV Analysis.*?(?=\n## \d|\Z)", re.DOTALL
        )
        if section_pattern.search(text):
            text = section_pattern.sub(NEW_SECTION_6.rstrip() + "\n\n---\n\n", text, count=1)
            changes.append("PRD: Bagian 6 diperbarui — tambah cv_content_hash & alur cache yang benar.")
        else:
            changes.append("PRD: PERINGATAN — section '## 6. Fitur CV Analysis' tidak ditemukan, dilewati.")

    # 2. Perbaiki klaim penghematan token tanpa sumber (kalau ada)
    if TOKEN_CLAIM_PATTERN.search(text):
        text = TOKEN_CLAIM_PATTERN.sub(TOKEN_CLAIM_REPLACEMENT, text, count=1)
        changes.append("PRD: klaim penghematan token tanpa sumber diganti jadi kualitatif.")

    # 3. Tambahkan section "Konflik Arsitektur & Keputusan Terbuka" sebelum
    #    baris "*Living document" penutup, kalau belum ada.
    if "Konflik Arsitektur & Keputusan Terbuka" in text:
        changes.append("PRD: section Konflik Arsitektur sudah ada — dilewati.")
    else:
        marker = re.search(r"\*Living document", text)
        if marker:
            insert_at = marker.start()
            text = text[:insert_at] + OPEN_DECISIONS_SECTION.rstrip() + "\n\n---\n\n" + text[insert_at:]
        else:
            text = text.rstrip() + "\n\n---\n\n" + OPEN_DECISIONS_SECTION.rstrip() + "\n"
        changes.append("PRD: section 11 'Konflik Arsitektur & Keputusan Terbuka' ditambahkan.")

    return text, changes


def patch_erd(text: str) -> tuple[str, list[str]]:
    changes = []

    if "CV_ANALYSIS_RESULTS" in text:
        changes.append("ERD: entity CV_ANALYSIS_RESULTS sudah ada — dilewati.")
        return text, changes

    mermaid_block = re.search(r"```mermaid\n(.*?)```", text, re.DOTALL)
    if not mermaid_block:
        changes.append("ERD: PERINGATAN — tidak menemukan blok ```mermaid``` di file, tidak ada yang diubah.")
        return text, changes

    body = mermaid_block.group(1)

    # Sisipkan relasi baru tepat setelah baris "erDiagram"
    if "erDiagram" in body:
        body = body.replace("erDiagram\n", "erDiagram\n" + ERD_NEW_ENTITY_BLOCK, 1)
    else:
        body = ERD_NEW_ENTITY_BLOCK + body

    # Tambahkan definisi entity baru di akhir blok mermaid
    body = body.rstrip() + "\n\n" + ERD_NEW_ENTITY_DEF

    new_mermaid = "```mermaid\n" + body.rstrip() + "\n```"
    text = text[: mermaid_block.start()] + new_mermaid + text[mermaid_block.end():]
    changes.append("ERD: entity CV_ANALYSIS_RESULTS + relasi USERS/JOBS ditambahkan.")

    return text, changes


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prd", required=True, help="Path ke PRD_JobMatch_AI.md")
    parser.add_argument("--erd", required=True, help="Path ke ERD_JobMatch_AI.md")
    parser.add_argument("--dry-run", action="store_true", help="Tampilkan rencana perubahan tanpa menulis file")
    args = parser.parse_args()

    prd_path = Path(args.prd)
    erd_path = Path(args.erd)

    if not prd_path.exists():
        print(f"ERROR: PRD tidak ditemukan di {prd_path}")
        sys.exit(1)
    if not erd_path.exists():
        print(f"ERROR: ERD tidak ditemukan di {erd_path}")
        sys.exit(1)

    prd_text = prd_path.read_text(encoding="utf-8")
    erd_text = erd_path.read_text(encoding="utf-8")

    new_prd_text, prd_changes = patch_prd(prd_text)
    new_erd_text, erd_changes = patch_erd(erd_text)

    print("=== Rencana perubahan ===")
    for c in prd_changes + erd_changes:
        print(f"  - {c}")

    if args.dry_run:
        print("\n[DRY RUN] Tidak ada file yang ditulis.")
        return

    if new_prd_text != prd_text:
        prd_path.write_text(new_prd_text, encoding="utf-8")
        print(f"\nDitulis: {prd_path}")
    if new_erd_text != erd_text:
        erd_path.write_text(new_erd_text, encoding="utf-8")
        print(f"Ditulis: {erd_path}")

    print("\nSelesai.")


if __name__ == "__main__":
    main()
