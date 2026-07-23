# PRD — JobMatch AI: Arsitektur & Panduan Teknis

**Project**: JobMatch AI (repo: `indri007/sweet-align-hub`, branch: `streamlit`)
**URL Live**: `https://jobsmatch.streamlit.app`
**Konteks**: Final Project JCAI — Job Connector AI Engineering, Purwadhika
**Disusun untuk**: Indri Kartikasari
**Terakhir diperbarui**: 21 Juli 2026

---

## 1. Ringkasan Eksekutif

JobMatch AI adalah aplikasi Streamlit berbasis multi-agent AI yang membantu pencari kerja di Indonesia:
- Analisis CV & skor ATS
- Rekomendasi lowongan (RAG via Qdrant)
- Review CV + generate CV format ATS (Bahasa Indonesia & Inggris)
- Konsultasi karir dengan referensi KPI & Salary Grade
- Simulasi wawancara berbasis kompetensi STAR

**Prinsip utama arsitektur**: Hemat token maksimal. Data statis (lowongan, aturan HRD, bank soal interview) di-*precompute* sekali ke Qdrant. LLM generatif **hanya** dipanggil untuk tugas reasoning: evaluasi jawaban, follow-up dinamis, saran perbaikan CV.

---

## 2. Arsitektur Sistem

### 2.1 Arsitektur Saat Ini (Live)

```
Browser User
     │
     ▼
Streamlit App (Streamlit Cloud — branch: streamlit)
     │
     ├──► LLM Provider (Groq rotating 4 keys / fallback Gemini Flash)
     │        └─ hanya untuk: evaluasi jawaban, saran CV, follow-up interview
     │
     ├──► Qdrant Cloud (vector_store.py)
     │        ├─ [1] indonesian_jobs_gemini     → 473 vektor loker
     │        ├─ [2] hr_knowledge_base           → 216 vektor aturan HRD + Excel
     │        ├─ [3] interview_questions_bank    → bank soal STAR (BARU)
     │        └─ [4] hr_memory / cs_memory       → memori refleksi agentic
     │
     └──► Aiven MySQL (database.py, SQLAlchemy)
               └─ jobs, user_profiles, cv_analysis_results
```

### 2.2 Arsitektur Target (Final: Python-Native)

Penyelesaian Konflik #2 telah memutuskan bahwa aplikasi tidak akan menggunakan N8N. Eksekusi `agent` dilakukan langsung melalui Python secara *native* menuju Gemini API dan Qdrant.

---

## 3. Tech Stack

| Layer | Teknologi |
|---|---|
| Frontend | Streamlit ≥ 1.39.0, Google OAuth (`st.login()`) |
| LLM Utama | Groq (llama-3.3-70b), 4 key rotasi |
| LLM Fallback | Gemini Flash (10 key rotasi) |
| Embedding | `models/text-embedding-004` via Gemini API (768-dim) |
| Vector DB | Qdrant Cloud (4 collections) |
| Relational DB | Aiven MySQL (SQLAlchemy + SSL) |
| TTS Leonardo | gTTS (gratis, tanpa API key, Bahasa Indonesia) |
| STT Voice Mode | OpenAI Whisper-1 (opsional) |
| Rekam Suara | `audio-recorder-streamlit` |
| Excel Parsing | `pandas` + `openpyxl` |
| Orkestrasi | Python-Native (LangChain / Gemini SDK) |
| Hosting | Streamlit Cloud (branch: streamlit) |

---

## 4. Qdrant Collections

| Collection | Isi | Jumlah | Dipakai Oleh |
|---|---|---|---|
| `indonesian_jobs_gemini` | Vektor loker + metadata | 473 | `rag_agent.py` — Step B |
| `hr_knowledge_base` | Keyword Bank, KPI, Salary Grade, Common Mistakes | 216 | `cv_analyzer_agent.py`, `career_agent.py` |
| `interview_questions_bank` | Bank soal STAR per kompetensi | ~41 | `interview_agent.py` — **BARU, precompute offline** |
| `hr_memory` | Refleksi insight sesi interview | Dinamis | `interview_agent.py` auto-append |

---

## 5. Fitur Mock Interview — Arsitektur Token-Efficient (BARU)

### Masalah Sebelumnya
Setiap sesi interview memanggil LLM generatif untuk *membuat* pertanyaan → **boros token, lambat, inkonsisten, kena 429 rate limit**.

### Solusi: Precompute Interview Bank ke Qdrant

#### FASE OFFLINE — Jalankan Sekali
```
Interview_Questions.xlsx (41 pertanyaan, 10 kompetensi STAR)
        │
        ▼ embed via Gemini text-embedding-004 (768-dim)
        │
        ▼ upsert ke Qdrant: "interview_questions_bank"

Payload per titik:
{
  "kompetensi": "Kemampuan Memecahkan Masalah (Problem Solving)",
  "tahap": "Situation",
  "pertanyaan": "Uraikan konteksnya: kapan, siapa yang terlibat, apa masalahnya..."
}
```
Script: `scripts/build_interview_kb.py`

#### FASE RUNTIME — Setiap Sesi Interview
```
1. User pilih posisi ("Finance Planning & Analysis Manager")
         │
         ▼
2. embed_text(cv_text + posisi) → 1x Embedding API call (murah)
         │
         ▼
3. Vector search ke Qdrant "interview_questions_bank"
   → ambil 6-8 pertanyaan terdekat berdasarkan CV + posisi
   ⚡ 0 panggilan LLM generatif
         │
         ▼
4. Tampilkan pertanyaan 1 per 1, Leonardo bacakan via gTTS
         │
         ▼
5. User menjawab (text / voice)
         │
         ▼
6. LLM dipanggil HANYA untuk:
   a. Evaluasi jawaban STAR (skor 1-5 per dimensi)
   b. Follow-up jika jawaban terlalu singkat
   c. Ringkasan akhir sesi (skor total per kompetensi)
```

#### Dampak Efisiensi Token

Pendekatan ini secara signifikan **mengurangi panggilan LLM untuk generate soal, karena diambil langsung dari Qdrant**. LLM hanya dipanggil untuk tugas penalaran tingkat tinggi (evaluasi jawaban kandidat), sehingga sangat menghemat penggunaan token LLM dan menurunkan risiko terkena *rate-limit*.

---

## 6. Fitur CV Analysis — Aiven Caching (Rencana)

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

---


## 7. Optimasi Token (Best Practices Terimplementasi)

| # | Strategi | Status |
|---|---|---|
| 1 | Interview questions dari Qdrant, bukan LLM generatif | ⏳ Proses (tunggu Qdrant key) |
| 2 | HR Knowledge dari Qdrant, bukan hardcode di prompt | ✅ Done |
| 3 | Rotating API keys (4 Groq + 10 Gemini) | ✅ Done |
| 4 | `max_tokens` per task disesuaikan (review=2500, ATS=3000) | ✅ Done |
| 5 | CV caching di Aiven (0 token untuk pembacaan ulang) | ⏳ Planned |
| 6 | Potong input CV ke 2000 char (cukup untuk match loker) | ⏳ Planned |

---

## 8. Environment Variables

| Var | Keterangan | Wajib? |
|---|---|---|
| `GEMINI_API_KEY` | Primary Gemini key | ✅ |
| `GEMINI_API_KEYS` | 10 key rotasi (comma-separated) | ✅ |
| `GROQ_API_KEY_1..4` | 4 key Groq rotasi | ✅ |
| `DATABASE_URL` | Aiven MySQL connection string | ✅ |
| `QDRANT_URL` | URL cluster Qdrant utama | ✅ |
| `QDRANT_API_KEY` | Key Qdrant (7 key baru, butuh write-access) | ✅ |
| `GEMINI_EMBEDDING_MODEL` | default `models/gemini-embedding-001` | opsional |
| `USE_N8N` | `false` (Deprecated, tidak dipakai) | ✅ |
| `OPENAI_API_KEY` | Wajib -- fallback LLM saat Gemini kena rate limit (dipakai llm_client.py, terverifikasi aktif di FR-15/FR-16) | ✅ |
| Google OAuth (`client_id`/`client_secret`) | Di `.streamlit/secrets.toml`, bukan `.env` | ✅ |

---

## 9. Checklist Validasi Akhir

- [ ] Upload CV → dapat rekomendasi lowongan dari Qdrant
- [ ] Review CV → skor ATS dengan rubrik baku (dari hr_knowledge_base)
- [ ] Generate CV ATS (Bahasa Indonesia & Inggris)
- [ ] **Interview Bank**: pertanyaan diambil dari Qdrant tanpa panggil LLM
- [ ] **Leonardo bersuara** via gTTS (tanpa OpenAI key)
- [ ] Rekam jawaban via `audio-recorder-streamlit`
- [ ] Evaluasi jawaban STAR via LLM (Groq/Gemini)
- [ ] Konsultasi karir referensi KPI & Salary Grade dari Qdrant
- [ ] Veronica CS menjawab pertanyaan tutorial

---

## 10. Backlog Prioritas

| Prioritas | Item | Status |
|---|---|---|
| 🔴 | Qdrant write-access key → jalankan `build_interview_kb.py` | Butuh key baru dari dashboard |
| 🔴 | Update `interview_agent.py` → `get_interview_questions()` dari Qdrant | Siap setelah ingest OK |
| 🔴 | Ganti TTS OpenAI → gTTS | Belum |
| 🟡 | Aiven caching CV Analysis Result | Schema sudah direncanakan |
| 🟡 | Common_Mistakes 6 poin + CV_Examples few-shot ke prompt | Belum |
| 🟡 | Token optimization: potong CV input 2000 char | Belum |
| 🟢 | Aktifkan `USE_N8N=true` + uji webhook end-to-end | Standby |

---

## 11. Konflik Arsitektur & Keputusan Terbuka

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

---

*Living document — diperbarui setiap ada perubahan arsitektur signifikan.*

## Keputusan Arsitektur: N8N vs Python-Native (Konflik #2 -- Ditutup)

**Tanggal keputusan**: 23 Juli 2026

**Keputusan**: Arsitektur produksi JobMatch AI menggunakan jalur Python-native
langsung (Streamlit -> agents/*.py -> Gemini/OpenAI + Qdrant + Aiven MySQL),
BUKAN N8N sebagai backbone orkestrasi. USE_N8N=false adalah konfigurasi final,
bukan sementara.

**Alasan**:
1. Seluruh FR-14 (filter Qdrant), FR-15 (state tracking multi-turn + guardrail),
   FR-16 (Evaluator label 3-tingkat), dan FR-17 (transkrip ke Aiven) sudah
   dibangun, diuji berlapis, dan terverifikasi jalan di jalur Python-native ini,
   termasuk verifikasi langsung ke Aiven MySQL produksi.
2. 6 file workflow N8N lama (n8n_workflows/*.json) dan JobMatch AI V3.json
   tidak pernah diperbaiki -- termasuk bug yang sudah teridentifikasi sejak
   awal (node yatim, risiko SQL injection, autentikasi tidak ter-wire, race
   condition dua CS agent). Migrasi ke N8N sekarang berarti membangun ulang
   seluruh logika yang sudah teruji tanpa jaminan kualitas yang sama.
3. n8n_client.py tetap ada di codebase sebagai jalur fallback opsional,
   tidak dihapus.

**Koreksi histori**: commit ffd5b41 sebelumnya menyebut "Migrasi Alur Chatbot
N8N ke Python Native" sebagai fait accompli sebelum keputusan ini resmi
diambil. Entri ini adalah keputusan resmi yang sebenarnya, dengan alasan
eksplisit.

**Item terbuka**: perlu dicek apakah rubrik penilaian JCAI mewajibkan N8N
sebagai kriteria formal. Jika ya, keputusan ini perlu dikonfirmasi ulang ke
pengajar/pembimbing sebelum submission final.
