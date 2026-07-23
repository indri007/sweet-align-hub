# PRD — JobMatch AI: Migrasi & Redeploy ke Laptop Baru

**Project**: JobMatch AI (folder lokal: `cvatsjob`)
**Service Cloud Run live**: `job-search-app` — project GCP `heaven-493814-f85dc`
**URL live**: `https://job-search-app-547610088942.asia-southeast2.run.app`
**Konteks**: Final Project JCAI — Job Connector AI Engineering, Purwadhika
**Disusun untuk**: Indri Kartikasari
**Tanggal**: 15 Juli 2026

---

## 1. Ringkasan Eksekutif

JobMatch AI adalah aplikasi Streamlit berbasis multi-agent AI yang membantu pencari kerja di Indonesia: analisis CV, rekomendasi lowongan (RAG via Qdrant), review CV, generate CV format ATS, konsultasi karir, dan simulasi wawancara. Dokumen ini adalah panduan teknis lengkap untuk memindahkan environment kerja dari Cloud Shell (`ravipridh88@cloudshell`) ke laptop baru, termasuk semua kode, dependency, environment variable, dan langkah redeploy ke Cloud Run.

**Status arsitektur saat ini**: aplikasi memanggil Gemini API, Qdrant, dan Aiven MySQL **langsung dari Python** (bukan lewat N8N webhook). Modul integrasi N8N (`n8n_client.py`, folder `n8n_workflows/`) sudah tersedia di kode tapi berstatus **nonaktif** (`USE_N8N=false`). Dokumen ini mencakup dua jalur: (A) redeploy versi yang jalan sekarang apa adanya, dan (B) langkah tambahan mengaktifkan N8N sesuai requirement rubrik JCAI.

---

## 2. Arsitektur Sistem

### 2.1 Arsitektur saat ini (live di Cloud Run)

```
Browser User
     │
     ▼
Streamlit App (Cloud Run, job-search-app)
     │
     ├──► Gemini API (google-genai SDK, model gemini-2.5-flash)
     │        └─ dipakai oleh: rag_agent, career_agent, cv_analyzer_agent,
     │                          sql_agent, interview_agent, customer_service_chat
     │
     ├──► Qdrant Cloud (vector_store.py)
     │        └─ collection job embeddings, dipakai untuk semantic search CV↔lowongan
     │
     └──► Aiven MySQL (database.py, via SQLAlchemy + ca.pem SSL)
              └─ menyimpan data lowongan terstruktur, query via sql_agent
```

### 2.2 Arsitektur target sesuai rubrik JCAI (N8N sebagai backbone)

```
Browser User
     │
     ▼
Streamlit App  ──POST──►  N8N Webhook (REST API, workflow published/Active)
                                │
                        AI Agent (LangChain node)
                          ├─► Groq/Gemini Chat Model
                          ├─► Vector Store Tool ──► Qdrant Vector Store node
                          └─► MySQL node ──► Aiven MySQL
```

Untuk beralih ke jalur ini, cukup set `USE_N8N=true` + `N8N_WEBHOOK_URL` di environment; `n8n_client.py` sudah punya fallback otomatis ke agent lokal kalau webhook tidak terjangkau.

---

## 3. Tech Stack

| Layer | Teknologi |
|---|---|
| Frontend/App | Streamlit, `st.login()` (Google OAuth native) |
| AI/LLM | Google Gemini 2.5 Flash (`google-genai` SDK) |
| Embedding | `models/gemini-embedding-001` |
| Vector DB | Qdrant Cloud |
| Relational DB | Aiven MySQL (SQLAlchemy, SSL via `ca.pem`) |
| Orkestrasi opsional | N8N (self-host / `n8n-student.purwadhika.com`) |
| OCR | Gemini Vision (fallback dari Tesseract) |
| TTS/Interview | gTTS, Gemini (fallback dari OpenAI Whisper/TTS — sudah di-stub) |
| Container | Docker (`python:3.10-slim` base, lihat `Dockerfile`) |
| Hosting | Google Cloud Run, region `asia-southeast2` |
| Voice bot (opsional) | Omnidim (env var masih placeholder, belum aktif) |

---

## 4. Prasyarat di Laptop Baru

```bash
# Cek versi yang dibutuhkan
python3 --version      # minimal 3.10
docker --version       # untuk build image lokal (opsional, testing)
git --version

# Install Google Cloud SDK (kalau belum ada)
# macOS:
brew install --cask google-cloud-sdk
# atau ikuti: https://cloud.google.com/sdk/docs/install

# Login & set project
gcloud auth login
gcloud config set project heaven-493814-f85dc
```

---

## 5. Struktur Folder Project (`cvatsjob`)

```
cvatsjob/
├── app.py                          # entry point Streamlit
├── config.py                       # load semua env var + client Gemini
├── database.py                     # koneksi Aiven MySQL (SQLAlchemy)
├── vector_store.py                 # koneksi Qdrant / ChromaDB
├── cv_processor.py                 # ekstraksi teks CV (PDF/DOCX/OCR)
├── auth_setup.py                   # Google OAuth setup untuk st.login()
├── customer_service_chat_floating.py
├── migrate_to_aiven.py             # migrasi data SQLite lokal → Aiven
├── scraper.py                      # scraping data lowongan baru
├── data_preparation.py
├── n8n_client.py                   # wrapper HTTP ke N8N webhook (fallback ke lokal)
├── agents/
│   ├── __init__.py
│   ├── rag_agent.py                # RAG: CV ↔ lowongan (Qdrant)
│   ├── career_agent.py             # konsultasi karir
│   ├── cv_analyzer_agent.py        # analisis & skor CV
│   ├── sql_agent.py                # natural language → SQL query
│   └── interview_agent.py          # simulasi wawancara
├── dataset/
│   └── jobs.jsonl                  # 473 lowongan (seed dataset)
├── aiven/
│   └── ca.pem                      # sertifikat SSL Aiven MySQL — WAJIB ADA
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml                # kredensial OAuth Google — JANGAN commit ke git
├── n8n_workflows/                  # 6 file JSON workflow N8N
│   ├── 1_cv_job_matcher.json
│   ├── 2_cv_reviewer.json
│   ├── 3_ats_cv_generator.json
│   ├── 4_career_consultant.json
│   ├── 5_mock_interview.json
│   └── 6_sql_agent.json
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

> **Catatan**: `aiven/ca.pem` dan `.streamlit/secrets.toml` (versi asli, bukan `.example`) perlu kamu salin manual dari sumber yang sudah kamu punya (tim/backup lama) — keduanya **tidak boleh** diketik ulang manual karena isinya kredensial biner/rahasia.

---

## 6. Environment Variables — Referensi Lengkap

Semua env var berikut **sudah kamu backup nilainya** ke folder `cloudrun-backup-f85dc/` dan `cloudrun-backup/secrets/` di Cloud Shell. Jangan copy-paste ulang raw value di dokumen ini — buka file `.txt` yang sesuai dari backup kamu.

| Env Var | Sumber nilai (file backup) | Wajib? |
|---|---|---|
| `GEMINI_API_KEY` | `cloudrun-backup-f85dc/job-search-app/service-config.yaml` | ✅ |
| `GEMINI_MODEL` | default `gemini-2.5-flash` (hardcoded fallback di `config.py`) | opsional |
| `GEMINI_EMBEDDING_MODEL` | default `models/gemini-embedding-001` | opsional |
| `DATABASE_URL` | `service-config.yaml` (project f85dc) | ✅ |
| `VECTOR_STORE` | `qdrant` (fixed) | ✅ |
| `QDRANT_URL` | `service-config.yaml` (project f85dc) | ✅ |
| `QDRANT_API_KEY` | `service-config.yaml` (project f85dc) | ✅ |
| `EMBEDDING_MODEL` | `local` (fixed, sesuai config live) | ✅ |
| `USE_N8N` | set manual `true`/`false` sesuai keputusan arsitektur (lihat §2) | ✅ |
| `N8N_WEBHOOK_URL` | `cloudrun-backup/secrets/N8N_WEBHOOK_URL.txt` | jika `USE_N8N=true` |
| `OMNIDIM_API_KEY` / `AGENT_ID` / `FROM_NUMBER_ID` | ⚠️ masih placeholder di live config — isi dari dashboard Omnidim kalau fitur ini dipakai, atau hapus kalau tidak | opsional |
| Google OAuth (`client_id`, `client_secret`, `cookie_secret`, `redirect_uri`) | `.streamlit/secrets.toml` asli | ✅ untuk fitur login |

Buat file `.env` lokal (untuk testing di laptop, bukan untuk Cloud Run):

```bash
cd cvatsjob
cat > .env << 'EOF'
GEMINI_API_KEY=isi_dari_backup
DATABASE_URL=isi_dari_backup
VECTOR_STORE=qdrant
QDRANT_URL=isi_dari_backup
QDRANT_API_KEY=isi_dari_backup
EMBEDDING_MODEL=local
USE_N8N=false
N8N_WEBHOOK_URL=isi_dari_backup_jika_dipakai
EOF
chmod 600 .env   # batasi permission, cuma owner yang bisa baca
```

---

## 7. Setup Lokal di Laptop Baru — Step by Step

### 7.1 Salin project dari backup

```bash
# Kalau kamu sudah punya zip backup (cloudrun-f85dc-backup.zip / cloudrun-full-backup.zip),
# extract dulu:
mkdir -p ~/projects
cd ~/projects
unzip ~/Downloads/cloudrun-f85dc-backup.zip -d jobmatch-restore
cd jobmatch-restore/source-cvatsjob
```

### 7.2 Buat virtual environment & install dependency

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 7.3 Jalankan lokal untuk testing

```bash
streamlit run app.py
# buka http://localhost:8501
```

### 7.4 Verifikasi koneksi ke masing-masing service

```bash
# Cek Qdrant
python3 - << 'EOF'
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv
load_dotenv()
client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
print(client.get_collections())
EOF

# Cek Aiven MySQL
python3 - << 'EOF'
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"), connect_args={"ssl": {"ca": "aiven/ca.pem"}})
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("Aiven MySQL OK:", result.fetchone())
EOF

# Cek Gemini
python3 - << 'EOF'
import os
from dotenv import load_dotenv
from google import genai
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
resp = client.models.generate_content(model="gemini-2.5-flash", contents="Halo, test koneksi.")
print(resp.text)
EOF
```

---

## 8. Redeploy ke Cloud Run dari Laptop Baru

```bash
# Pastikan sudah login & project benar
gcloud auth login
gcloud config set project heaven-493814-f85dc

# Deploy langsung dari source folder (Cloud Build otomatis buat image)
cd ~/projects/jobmatch-restore/source-cvatsjob

gcloud run deploy job-search-app \
  --source . \
  --region asia-southeast2 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 3 \
  --set-env-vars="GEMINI_API_KEY=xxx,DATABASE_URL=xxx,VECTOR_STORE=qdrant,QDRANT_URL=xxx,QDRANT_API_KEY=xxx,EMBEDDING_MODEL=local,USE_N8N=false"
```

> Ganti tiap `xxx` dengan nilai asli dari file backup kamu — **jangan** commit command dengan value asli ke Git/catatan publik manapun.

Verifikasi setelah deploy:

```bash
gcloud run services describe job-search-app --region=asia-southeast2 --format="value(status.url)"
curl -I <url_yang_muncul>
```

---

## 9. Mengaktifkan N8N (jika diwajibkan rubrik)

### 9.1 Import workflow ke instance N8N

1. Buka `https://n8n-student.purwadhika.com` (atau instance self-host kamu di VPS `ubuntu007`)
2. Menu **Workflows → Import from File**, upload satu per satu:
   - `1_cv_job_matcher.json`
   - `2_cv_reviewer.json`
   - `3_ats_cv_generator.json`
   - `4_career_consultant.json`
   - `5_mock_interview.json`
   - `6_sql_agent.json`
3. Untuk tiap workflow, buka node **Qdrant Vector Store** dan **MySQL**, isi ulang credential (URL/API key) sesuai environment kamu.
4. Klik toggle **Active** di kanan atas tiap workflow — pastikan berubah hijau.
5. Catat URL webhook tiap workflow (klik node Webhook → Production URL).

### 9.2 Update Cloud Run untuk pakai N8N

```bash
gcloud run services update job-search-app \
  --region asia-southeast2 \
  --update-env-vars="USE_N8N=true,N8N_WEBHOOK_URL=https://n8n-student.purwadhika.com"
```

### 9.3 Test webhook manual sebelum full-integration

```bash
curl -X POST https://n8n-student.purwadhika.com/webhook/job-match \
  -H "Content-Type: application/json" \
  -d '{"cv_text": "Data Analyst dengan 2 tahun pengalaman SQL dan Python", "jobs_context": ""}'
```

---

## 10. Checklist Validasi Akhir

- [ ] `aiven/ca.pem` ada di folder project (bukan cuma di `.env.example`)
- [ ] `.streamlit/secrets.toml` asli (bukan `.example`) sudah terisi kredensial OAuth
- [ ] `streamlit run app.py` jalan lokal tanpa error koneksi
- [ ] Login Google OAuth berhasil
- [ ] Upload CV → dapat rekomendasi lowongan (test RAG + Qdrant)
- [ ] Fitur chat konsultasi karir merespons
- [ ] Fitur SQL agent bisa jawab pertanyaan seputar salary/work_type
- [ ] Mock interview (voice/text) berjalan
- [ ] `gcloud run deploy` sukses, `curl -I <url>` return 200
- [ ] `OMNIDIM_*` sudah diisi asli atau dihapus dari env vars kalau tidak dipakai

---

## 11. Rekomendasi Keamanan Sebelum & Sesudah Migrasi

1. **Rotate semua kredensial** setelah migrasi selesai dan dikonfirmasi jalan di laptop baru:
   - Aiven MySQL: reset password user `avnadmin` via Aiven Console
   - Google AI Studio: regenerate `GEMINI_API_KEY`
   - Qdrant Cloud: regenerate API key di dashboard
   - N8N: hapus & generate ulang API token lama
2. Simpan file `.env` dan `secrets.toml` dengan permission terbatas (`chmod 600`), jangan commit ke Git — pastikan `.gitignore` mencakup keduanya (sudah ada di project kamu).
3. Setelah laptop lama tidak dipakai lagi untuk project ini, hapus salinan `.env`/`secrets.toml`/`ca.pem` dari sana.

---

## 12. Item Terbuka (Belum Terselesaikan — Perlu Keputusan Kamu)

| Item | Aksi yang dibutuhkan |
|---|---|
| "Main agent" tunggal terpisah dari RAG/SQL agent | Perlu didesain ulang kalau reviewer strict soal ini |
| Salinan pptx presentasi milik sendiri | Pastikan kamu punya, bukan cuma dari file teman satu tim |

*Catatan: Isu Konflik #2 (Arsitektur N8N vs Python-native) telah FINAL diputuskan menggunakan 100% Python-native. Isu deduplikasi data `jobs.jsonl` juga telah dibersihkan.*

---

*Dokumen ini disusun berdasarkan riwayat kerja dan konfigurasi yang sudah diverifikasi langsung dari Cloud Shell (`heaven-493814` & `heaven-493814-f85dc`) serta dokumen rubrik resmi Final Project JCAI — Purwadhika.*
