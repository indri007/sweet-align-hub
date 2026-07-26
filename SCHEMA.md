# Skema Data JobMatch AI (Sesuai PRD V3.0)

Dokumen ini menjabarkan seluruh skema data yang saat ini aktif dan ter- *deploy* di ekosistem JobMatch AI, yang terdiri dari **Aiven MySQL** (Data Relasional) dan **Qdrant Cloud** (Vector/Semantic Data).

## 1. Relational Database (Aiven MySQL)

Tabel-tabel di bawah ini diakses dan dikelola baik melalui ORM (SQLAlchemy di `database.py`) maupun eksekusi SQL langsung (seperti saat Ingestion Knowledge Base).

### A. Core Tables (via SQLAlchemy)
- **`jobs`**: Menyimpan data lowongan kerja.
  - Kolom: `id`, `job_title`, `company_name`, `location`, `work_type`, `salary_raw`, `salary_min`, `salary_max`, `job_description`, `scrape_timestamp`
- **`hrd_transcripts`**: Menyimpan log sesi wawancara (Mock Interview).
  - Kolom: `id`, `session_id`, `email`, `posisi`, `transcript_json`, `evaluation_result`, `completed`, `created_at`

### B. ATS Knowledge Base Tables (via SQL Migration)
Sistem *CV Generator* dan *CV Analyzer* mengacu pada tabel-tabel ini (termasuk *scoring rubric*) sesuai rancangan §5.4 dan §11 PRD:
- **`scoring_rubric`**: Master kriteria penilaian (14 kriteria).
  - Kolom: `rubric_id`, `dimension`, `criterion`, `max_points`, `weight`, `rule_type`
- **`cv_red_flags`**: Tanda bahaya/kesalahan umum dalam CV.
  - Kolom: `flag_id`, `flag_name_id`, `flag_name_en`, `description_id`, `description_en`, `severity`, `fix_suggestion_id`, `fix_suggestion_en`
- **`action_verbs`**: Kata kerja kuat untuk perbaikan CV.
  - Kolom: `verb_id`, `verb_id_lang`, `verb_en_lang`, `category`
- **`rewrite_examples`**: Contoh penulisan CV *before-after*.
  - Kolom: `example_id`, `function_id`, `before_text_id`, `after_text_id`, `before_text_en`, `after_text_en`, `principle`
- **`skills`**, **`job_functions`**, **`job_levels`**: Taksonomi fungsi pekerjaan dan *skill* yang terkait.
- **`cv_scoring_history`**: Log histori penilaian CV oleh *Analyzer*.

---

## 2. Vector Database (Qdrant Cloud)

Arsitektur telah bergeser ke **100% Python-Native** yang memusatkan semua indeks pencarian semantik ke satu sumber provider LLM saja (Google Gemini dengan dimensi 768).

### Collection Utama:
- **`indonesian_jobs_gemini`** (Dimensi: 768)
  - **Fungsi:** Menyimpan hasil *embedding* dari tabel `jobs` (Aiven) agar LLM bisa melakukan *Semantic Search* (RAG) saat pengguna mencari lowongan dengan *natural language*.
  - **Model:** `models/gemini-embedding-001`

- **`hrd_knowledge`** (Dimensi: 768)
  - **Fungsi:** Menyimpan dokumen kebijakan HRD, FAQ, dan pengetahuan teknis bagi Agen CS (Veronika) dan Agen HRD (Leonardo).
  - **Model:** `models/gemini-embedding-001`

> **Catatan Sejarah (Deprecated):** 
> Collection lama bernama `indonesian_jobs_n8n` (384-dim) atau koleksi berbasis OpenAI (1536-dim) sudah dinonaktifkan sepenuhnya dari arsitektur sejalan dengan keputusan mempensiunkan *pipeline* N8N.
