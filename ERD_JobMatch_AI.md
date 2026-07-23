## Entity‑Relationship Diagram (ERD)

Berikut diagram ERD utama yang menggambarkan tabel‑tabel inti dalam database MySQL Aiven.

```mermaid
erDiagram
    JOBS {
        int id PK "Job ID"
        varchar title "Judul"
        varchar company "Perusahaan"
        varchar location "Lokasi"
        text description "Deskripsi"
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
```
