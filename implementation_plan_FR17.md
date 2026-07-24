# Implementation Plan: FR-17 (Transkrip Aiven MySQL)

Dokumen ini merangkum rencana arsitektur dan implementasi untuk menyimpan riwayat wawancara dan hasil evaluasinya ke database Aiven MySQL, mengadopsi 3 saran desain dari Anda.

## 1. Analisis & Validasi Saran Anda Terhadap Sistem Saat Ini

### A. Penggunaan `user_id` (Numeric) vs `email`
- **Kondisi Saat Ini**: Sistem (seperti terlihat di `app.py`, `auth_setup.py`, dan PRD) mengandalkan `st.user.email` sebagai identitas primer karena sistem login menggunakan bawaan Google OAuth dari Streamlit. Belum ada tabel `users` di `database.py`.
- **Validasi**: Saran Anda **sangat valid dan krusial**. Menyimpan email secara redundan di banyak tabel (seperti di `cv_analysis_results` sebelumnya) menyalahi normalisasi dan berisiko jika user mengganti email.
- **Langkah Kedepan**: Kita akan membuat tabel `users` sebagai *Single Source of Truth* untuk pengguna. Sebelum sesi wawancara disimpan, kita akan melakukan "Get or Create" ke tabel `users` menggunakan email untuk mendapatkan `user_id` (angka), lalu menyimpannya sebagai *foreign key* di tabel transkrip.

### B. Penggunaan Tipe Kolom `JSON` Native
- **Kondisi Saat Ini**: Transkrip wawancara direpresentasikan sebagai list of dicts (`session.turns`), dan hasil evaluasi FR-16 adalah objek JSON.
- **Validasi**: Aiven MySQL menggunakan MySQL 8.0+ yang mendukung penuh tipe kolom `JSON`. Ini **jauh lebih baik** dari sekadar `LONGTEXT` karena MySQL akan menolak string yang bukan JSON valid, sehingga menjaga integritas data secara mutlak.
- **Langkah Kedepan**: Menggunakan tipe data `sqlalchemy.JSON` untuk mendefinisikan kolom `transcript_json` dan `evaluation_result` di SQLAlchemy.

### C. Auto-Trigger Penyimpanan
- **Kondisi Saat Ini**: Di `pages/step_e_interview.py`, saat wawancara selesai, aplikasi langsung memanggil Agen 6 untuk evaluasi dan menampilkan hasilnya ke UI.
- **Validasi**: Valid. Menambahkan tombol "Simpan" adalah *anti-pattern* UX modern untuk data transaksional berharga. Jika tab tertutup, komputasi LLM yang mahal akan terbuang sia-sia tanpa jejak.
- **Langkah Kedepan**: Logika *insert* ke database akan diletakkan langsung di dalam blok yang menangani `session.completed == True`, persis setelah Evaluator (Agen 6) berhasil mengeluarkan skor JSON-nya.

---

## 2. Rencana Perubahan Kode (Proposed Changes)

### Database Layer (`database.py`)
- **[NEW] Tabel `User`**:
  - `id`: Integer, Primary Key, Auto Increment
  - `email`: String, Unique, Not Null
  - `created_at`: String (Timestamp)
- **[NEW] Tabel `HrdTranscript`**:
  - `id`: Integer, Primary Key, Auto Increment
  - `session_id`: String(36), Unique
  - `user_id`: Integer, ForeignKey(`users.id`)
  - `posisi`: String
  - `transcript_json`: JSON
  - `evaluation_result`: JSON
  - `completed`: Boolean
  - `created_at`: String (Timestamp)
- **[NEW] Fungsi**:
  - `get_or_create_user(email: str) -> int`: Mencari `user_id` berdasarkan email. Jika belum ada, buat baru.
  - `save_hrd_transcript(user_id: int, session: InterviewSession)`: Menyimpan data dari dataclass sesi ke database menggunakan kolom JSON native.

### UI / Presentation Layer (`pages/step_e_interview.py`)
- **[MODIFY] Integrasi Auto-Save**:
  - Menarik fungsi `save_hrd_transcript` dan `get_or_create_user`.
  - Di dalam blok `if session.completed:`, setelah `result = evaluate_interview(...)` sukses dijalankan, dapatkan `user_id` kandidat (`st.user.email`).
  - Eksekusi `save_hrd_transcript(...)` secara sekuensial. Jika *database error*, tangkap *exception*-nya agar UI tidak *crash*, namun catat di log sistem.

## 3. User Review Required

> [!IMPORTANT]
> Karena perubahan ini akan membuat tabel baru (`users` dan `hrd_transcripts`) di Aiven MySQL Anda:
> 1. Apakah Anda setuju dengan skema penambahan tabel `users` ini? 
> 2. Apakah Anda siap untuk meninjau perubahan ini secara langsung ke database Aiven, atau apakah Anda ingin saya menyertakan `test_script` lokal menggunakan SQLite in-memory dulu untuk membuktikan fungsi kerjanya?

Silakan klik **Proceed** jika Anda menyetujui rencana ini!
