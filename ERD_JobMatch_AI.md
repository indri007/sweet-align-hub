## 1. Entity-Relationship Diagram (ERD) - Relational DB (Aiven MySQL)

Berikut diagram ERD utama yang menggambarkan tabel-tabel inti dalam database MySQL Aiven secara aktual berdasarkan implementasi di `database.py`.

```mermaid
erDiagram
    JOBS {
        int id PK "Job ID"
        varchar job_title "Judul"
        varchar company_name "Perusahaan"
        varchar location "Lokasi"
        varchar work_type "Tipe Kerja"
        varchar salary_raw "Gaji Mentah"
        float salary_min "Gaji Minimum"
        float salary_max "Gaji Maksimum"
        text job_description "Deskripsi"
        varchar scrape_timestamp "Timestamp Scrape"
    }

    HRD_TRANSCRIPTS {
        int id PK
        varchar session_id UK "UUID Sesi Wawancara"
        varchar email "Menyambung ke Users/Email"
        varchar posisi "Posisi yang dilamar"
        json transcript_json "Log percakapan QA"
        json evaluation_result "Skor/Feedback final"
        boolean completed "Status Selesai"
        datetime created_at "Waktu Dibuat"
    }
```

*(Catatan: Tabel USERS, APPLICATIONS, CVS, dan CV_ANALYSIS_RESULTS sebelumnya merupakan rancangan awal (planned), namun secara aktual pada rilis ini hanya 2 tabel di atas yang diaktifkan sebagai tabel inti)*

---

## 2. Vector Collections Schema (Qdrant Cloud)

Berikut adalah struktur koleksi vektor aktual di Qdrant yang menggunakan *embedding* Gemini (`models/gemini-embedding-001`, dimensi 768) sesuai dengan arsitektur Python-Native terkini:

```mermaid
erDiagram
    QDRANT_CLOUD ||--o{ GEMINI_EMBEDDING : "Primary (Gemini 768-dim)"

    GEMINI_EMBEDDING {
        varchar indonesian_jobs_gemini "Vektor Lowongan Kerja"
        varchar hrd_knowledge "Vektor Aturan HRD & KPI"
    }
```
