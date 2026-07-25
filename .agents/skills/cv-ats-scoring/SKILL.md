---
name: cv-ats-scoring
description: Use when working on CV/resume parsing, ATS scoring logic, CV generation, or OCR extraction (Gemini Vision) in the cvatsjob project.
---

# CV Analysis & ATS Scoring

## Alur kerja fitur ini
1. Upload CV (PDF/gambar) → OCR via Gemini Vision untuk ekstrak teks
2. Teks CV diproses `gemini-2.5-flash` untuk parsing struktur (skill, pengalaman, pendidikan)
3. Dibandingkan dengan job description → hasil ATS score
4. Hasil dirender ke PDF (CV builder module)

## Yang harus diperhatikan
- **Bug diketahui**: rendering PDF kadang gagal/rusak untuk CV dengan format tertentu — cek dulu apakah perubahan kamu bikin ini makin parah
- Akurasi parsing masih jadi concern — kalau ubah prompt parsing, uji dengan beberapa contoh CV nyata (format Indonesia & Inggris), bukan cuma satu kasus
- Jangan generate ulang keseluruhan CV di setiap re-scoring — cache hasil parsing kalau input CV sama, biar hemat token panggilan Gemini

## Efisiensi token
- Prompt scoring sebaiknya kirim ringkasan hasil parsing (bukan full raw OCR text) ke tahap scoring, supaya tidak dobel proses
- Batasi output Gemini dengan struktur JSON yang jelas (skema tetap), biar gampang parse & gak ada token boros buat teks pembuka/penutup

## Testing sebelum bilang "selesai"
- Test dengan CV yang formatnya beda-beda (single column, dua kolom, ada gambar/logo)
- Pastikan skor ATS konsisten untuk input yang sama (idempotent)
- Cek PDF hasil generate bisa dibuka normal di Adobe Reader & browser
