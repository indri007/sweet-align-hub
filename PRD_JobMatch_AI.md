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

### 2.2 Arsitektur Target (N8N Backbone — Standby)

```
Streamlit App ──POST──► N8N Webhook (n8n.kelasantai.online)
                              │
                    Orchestrator Agent
                      ├─► Groq/Gemini Chat
                      ├─► Qdrant Vector Store Tool
                      └─► Aiven MySQL Tool
```

Aktifkan dengan `USE_N8N=true` di Streamlit Cloud Secrets.

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
| Orkestrasi | N8N self-host (`n8n.kelasantai.online`) — standby |
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
| Aksi | Sebelum | Sesudah |
|---|---|---|
| Generate 6 pertanyaan | ~1200 token LLM | **0 token** (Qdrant) |
| Evaluasi 1 jawaban | ~1200 token | ~600 token |
| Total per sesi | ~8.000 token | **~3.000 token (hemat 62%)** |

---

## 6. Fitur CV Analysis — Aiven Caching (Rencana)

Hasil AI disimpan permanen ke tabel `cv_analysis_results` di Aiven:

| Kolom | Isi |
|---|---|
| `email` | Identitas user |
| `language` | `id` / `en` (simpan versi terpisah, tidak saling timpa) |
| `job_title`, `job_description` | Loker target |
| `hr_knowledge_context` | Referensi HRD dari Qdrant yang dipakai AI |
| `ats_score` | Skor ATS hasil analisis |
| `cv_feedback` | Kelebihan, kekurangan, saran |
| `ats_cv_text` | Teks CV versi ATS-friendly |
| `created_at` | Timestamp |

**Alur runtime:**
1. Cek Aiven → jika ada → tampilkan langsung (**0 token**)
2. Jika belum ada → panggil LLM → simpan ke Aiven → tampilkan

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
| `GOOGLE_CLIENT_ID/SECRET` | OAuth Google Login | ✅ |
| `N8N_WEBHOOK_URL` | `https://n8n.kelasantai.online` | jika `USE_N8N=true` |
| `USE_N8N` | `false` default | ✅ |
| `OPENAI_API_KEY` | Opsional, untuk Whisper STT | opsional |

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

*Living document — diperbarui setiap ada perubahan arsitektur signifikan.*
