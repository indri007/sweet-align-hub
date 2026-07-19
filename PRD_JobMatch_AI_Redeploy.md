# PRD — JobMatch AI: Arsitektur Enterprise (v2.0)

**Project**: JobMatch AI (Update 19 Juli 2026)
**URL Live (Streamlit Cloud)**: `https://jobsmatch.streamlit.app`
**Konteks**: Final Project JCAI — Job Connector AI Engineering, Purwadhika
**Disusun untuk**: Indri Kartikasari

---

## 1. Ringkasan Eksekutif (Update Terbaru)

JobMatch AI telah berevolusi dari sekadar purwarupa menjadi aplikasi berarsitektur **Enterprise**. Update terbaru (Juli 2026) menghadirkan tiga pilar utama:
1. **Multi-LLM Routing**: Tidak lagi bergantung pada satu AI. Sistem secara dinamis bisa beralih antara Groq (Llama 3.3), Google Gemini, OpenRouter, dan Mistral.
2. **Data Streaming**: Seluruh aktivitas agen dan log persona pengguna kini dialirkan secara *real-time* ke **Aiven Kafka**, membuka jalan untuk *Machine Learning* lanjutan dan analitik data.
3. **Dual Automation Engine**: Aplikasi kini memiliki 2 jalur operasi: Eksekusi Python Langsung (Sangat Cepat) ATAU Orkestrasi Webhook via **N8N** (untuk otomatisasi alur kerja).

Dokumen ini adalah panduan teknis lengkap yang mencakup konfigurasi terbaru, penambahan Kafka, serta metode peluncuran ke Github & Streamlit Cloud.

---

## 2. Arsitektur Sistem (Versi 2.0)

### 2.1 Arsitektur Utama (Python Direct + Kafka Data Asset)

```
Browser User
     │
     ▼
Streamlit Cloud App (Cabang Github: 'streamlit')
     │
     ├──► Unified LLM Client (llm_client.py)
     │        ├─► Groq Cloud (llama-3.3-70b-versatile) ── (Utama)
     │        ├─► Google Gemini 2.5 Flash
     │        └─► OpenRouter / Mistral (Fallback)
     │
     ├──► Qdrant Cloud (vector_store.py)
     │        └─ Semantic search CV ↔ Lowongan (gemini-embedding-001)
     │
     ├──► Aiven MySQL (database.py)
     │        └─ Basis data lowongan relasional (Query lewat SQL Agent)
     │
     └──► Aiven Kafka (kafka_producer.py) ── [FITUR BARU]
              └─ Log interaksi, analitik CV, dan user persona direkam sebagai 'Data Asset'.
```

### 2.2 Arsitektur Orkestrasi (N8N Webhook) - Opsi Alternatif

Sistem N8N Client lama telah direstorasi (`n8n_client.py`). Jika opsi ini diaktifkan di konfigurasi, Streamlit tidak akan memanggil LLM secara langsung, melainkan:

```
Streamlit App  ──POST──►  N8N Webhook (REST API)
                                │
                          N8N Workflow Nodes
                           ├─► LangChain LLM Node
                           ├─► Qdrant Vector Store Node
                           └─► MySQL Node
```
Untuk beralih ke jalur ini, cukup ubah `USE_N8N="true"` dan isi `N8N_WEBHOOK_URL` di *secrets* Streamlit.

---

## 3. Tech Stack Terbaru

| Layer | Teknologi |
|---|---|
| Frontend/App | Streamlit, `st.login()` (Google OAuth native) |
| AI/LLM | **Groq (Llama 3.3)**, Google Gemini, OpenRouter, Mistral |
| Embedding | `models/gemini-embedding-001` (Qdrant Cloud) |
| Relational DB | Aiven MySQL (SQLAlchemy, SSL via `ca.pem`) |
| Data Streaming | **Aiven Kafka** (Topic: `interview-logs`, `step_b_jobs`, `persona_logs`) |
| Orkestrasi | N8N Webhook Client (Opsional) |
| Hosting Utama | **Streamlit Cloud** (Auto-deploy dari Github cabang `streamlit`) |
| Hosting Alternatif | Google Cloud Run (Opsional via Docker) |

---

## 4. Environment Variables — Referensi Lengkap (Rahasia)

Berikut adalah daftar variabel lingkungan yang wajib ada di Streamlit Cloud (Format TOML) maupun file `.env` lokal Anda:

### Database & Infrastruktur
- `DATABASE_URL`: URI Aiven MySQL.
- `KAFKA_URI`: `kafka-3dfd3f26-indri-b983.i.aivencloud.com:19453`
- `KAFKA_USERNAME` / `KAFKA_PASSWORD`: Kredensial Aiven Kafka.
- `QDRANT_URL` / `QDRANT_API_KEY`: Kredensial cluster Qdrant.

### Multi-LLM API Keys
- `GEMINI_API_KEY`: (Google)
- `GROQ_API_KEY`: (Groq Cloud) - *Prioritas Utama*
- `OPENROUTER_API_KEY`: (OpenRouter)
- `MISTRAL_API_KEY`: (Mistral)
- `LLM_PROVIDER`: Set menjadi `"groq"`, `"gemini"`, atau `"openrouter"`.

### Automation & OAuth
- `N8N_API_KEY` / `N8N_WEBHOOK_URL` / `USE_N8N`: Kendali fitur N8N.
- Kredensial Google OAuth (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, dll).

---

## 5. Deployment Guide: Streamlit Cloud (Revisi 2.0)

Saat ini proyek menggunakan metode Continuous Deployment (CD) dari GitHub ke Streamlit Cloud.

**Langkah Deploy / Update:**
1. Lakukan perubahan kode lokal.
2. *Commit* dan *Push* ke Github di cabang `streamlit`:
   `git add . && git commit -m "update" && git push origin streamlit`
3. Buka Dashboard Streamlit Cloud.
4. Buka **Settings** -> **Secrets**.
5. *Copy-Paste* isi dari `streamlit_secrets.toml` ke kotak teks hitam, lalu klik **Save**.
6. Streamlit akan memuat ulang aplikasi secara otomatis. File `ca.pem` (Sertifikat Kafka/MySQL) dan dependensi `confluent-kafka` sudah dibungkus dan diunduh otomatis dari `requirements.txt`.

---

## 6. Setup Lokal di Laptop Baru (Extract dari jobnew.zip)

Jika Anda baru saja memindahkan `jobnew.zip` ke laptop baru (Windows/Mac 1TB):
1. Ekstrak *file* `jobnew.zip`.
2. Buka terminal di dalam folder ekstraksi.
3. Jalankan perintah instalasi dependensi:
   ```bash
   python -m venv venv
   source venv/bin/activate  # (atau venv\Scripts\activate untuk Windows)
   pip install -r requirements.txt
   ```
4. Pastikan file `.env` dan `ca.pem` sudah ter-ekstrak dengan baik (kedua file tersebut sudah saya pastikan masuk ke dalam zip).
5. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```

---

## 7. Checklist Validasi Arsitektur V2

- [x] Multi-LLM berhasil diimplementasikan (`llm_client.py` merespons Groq/Gemini).
- [x] Kafka Producer terhubung tanpa *crash* (`confluent-kafka` sukses, `ca.pem` divalidasi).
- [x] Log wawancara & interaksi CV ditembakkan ke Aiven 2 (Kafka).
- [x] Script integrasi `n8n_client.py` sukses direstorasi dan anti-crash.
- [x] Secrets dikonversi ke format TOML untuk Streamlit Cloud.
- [x] Kode dibersihkan dari *hardcoded password* (bersih di Github).

---
*End of Document - Arsitektur V2.0 siap untuk dinilai.*
