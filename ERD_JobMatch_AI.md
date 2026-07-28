## 1. Entity‑Relationship Diagram (ERD) - Relational DB (Aiven MySQL)

Berikut diagram ERD utama yang menggambarkan tabel‑tabel inti dalam database MySQL Aiven, diperbarui sesuai dengan PRD V4 (100% Python-Native).

```mermaid
erDiagram
  USERS ||--o{ CV_ANALYSIS_RESULTS : requests
  JOBS ||--o{ CV_ANALYSIS_RESULTS : analyzed_against
  
    JOBS {
        int id PK "Job ID"
        varchar job_title "Judul"
        varchar company_name "Perusahaan"
        varchar location "Lokasi"
        varchar work_type "Tipe Pekerjaan"
        float salary_min "Gaji Minimum"
        float salary_max "Gaji Maksimum"
        text job_description "Deskripsi"
        date posted_date "Tanggal posting"
    }
    USERS {
        int id PK "User ID"
        varchar email "Email"
        varchar name "Nama"
        varchar role "Peran"
    }
    APPLICATIONS {
        int id PK "Application ID"
        int user_id FK "User ID"
        int job_id FK "Job ID"
        datetime applied_at "Waktu apply"
        varchar status "Status"
    }
    CVS {
        int id PK "CV ID"
        int user_id FK "User ID"
        text content "Isi CV"
        datetime uploaded_at "Waktu upload"
    }

    USERS ||--o{ APPLICATIONS : "applies"
    JOBS ||--o{ APPLICATIONS : "receives"
    USERS ||--o{ CVS : "uploads"
    CVS ||--o{ APPLICATIONS : "references"
    USERS ||--o{ HRD_TRANSCRIPTS : "undergoes"

    HRD_TRANSCRIPTS {
        int id PK
        varchar session_id UK "UUID Sesi Wawancara"
        varchar email FK "Menyambung ke Users/Email"
        varchar posisi "Posisi yang dilamar"
        json transcript_json "Log percakapan QA"
        json evaluation_result "Skor/Feedback final"
        boolean completed "Status Selesai"
        datetime created_at
    }

  CV_ANALYSIS_RESULTS {
    string cv_content_hash PK "SHA-256 dari teks CV ter-parse"
    string email FK "Identitas user"
    string job_id FK "Loker target"
    string language "id / en"
    text hr_knowledge_context "Referensi HRD dari Qdrant"
    float ats_score "Skor ATS hasil analisis"
    text cv_feedback "Kelebihan, kekurangan, saran"
    text ats_cv_text "Teks CV versi ATS-friendly"
    datetime created_at
  }

  SCORING_RUBRIC {
    int id PK
    varchar criteria "Kriteria Penilaian (ATS/Konten/Match)"
    float weight "Bobot"
    text description "Deskripsi Indikator"
  }

  CS_AGENT_LOG {
    int id PK
    varchar agent_name "Nama Agent (Veronika/Leonardo)"
    varchar session_id "ID Sesi"
    text query "Pertanyaan User"
    text response "Jawaban Agent"
    datetime created_at "Waktu Log"
  }
```

---

## 2. Vector Collections Schema (Qdrant Cloud)

Sesuai dengan pembaruan PRD V4 (100% Python-Native), pendekatan OpenAI Fallback telah **dihapus sepenuhnya**. Berikut adalah struktur koleksi vektor di Qdrant yang menggunakan Gemini Embedding (gemini-embedding-001, 768-dim):

```mermaid
erDiagram
    QDRANT_CLOUD ||--o{ PRIMARY_GEMINI : "Collections (Gemini 768-dim)"

    PRIMARY_GEMINI {
        varchar indonesian_jobs_gemini "Job Database (Judul + Deskripsi, 499 point)"
        varchar hrd_knowledge "Knowledge Base HRD (SOP, Training, Scoring, dll)"
        varchar cs_memory "Memori / Log FAQ untuk Agent CS (Veronika)"
        varchar interview_questions_bank "Bank Soal STAR Interview (Precomputed)"
    }
```
