# PRD — JobMatch AI: Riwayat Migrasi & Redeploy (Arsip)

> **Catatan**: Dokumen ini adalah arsip proses migrasi dari arsitektur Google
> Cloud Run (versi awal project) ke Streamlit Community Cloud (arsitektur
> final saat ini). Untuk dokumentasi PRD aktif, lihat `PRD_JobMatch_AI.md`
> di folder utama `sweet-align-hub-extracted`. Seluruh referensi ke
> akun/project GCP spesifik pada dokumen asli telah dihapus dari versi
> arsip ini.

## Ringkasan

Project ini pada awalnya dikembangkan dan di-deploy menggunakan Google Cloud
Run sebagai hosting, dengan environment kerja awal di Google Cloud Shell.
Proses migrasi memindahkan seluruh kode dan environment kerja ke laptop lokal,
lalu arsitektur hosting dipindahkan sepenuhnya ke Streamlit Community Cloud.

## Status Arsitektur Final

Lihat `PRD_JobMatch_AI.md` di folder `sweet-align-hub-extracted` untuk detail
lengkap arsitektur final:
- Hosting: Streamlit Community Cloud
- Orkestrasi: Python-native (bukan N8N)
- Database: Aiven MySQL
- Vector search: Qdrant Cloud

---

*Dokumen asli (versi Cloud Run) diarsipkan sebagai referensi historis proses
migrasi. Seluruh kredensial, nama project GCP, dan detail akun spesifik pada
dokumen asli telah dihapus dari versi ini.*
