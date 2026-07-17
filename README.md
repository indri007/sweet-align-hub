# 🎯 JobMatch AI — CV Review & Job Recommendation App

AI-powered web application untuk membantu pencarian kerja di Indonesia.
Upload CV kamu dan dapatkan rekomendasi lowongan, review CV, konsultasi karir, dan mock interview ini berbasis AI.

## 🌐 Live Demo

**[https://difi-547610088942.asia-southeast2.run.app](https://difi-547610088942.asia-southeast2.run.app)**

## ✨ Fitur

- 📄 **Upload CV** — Mendukung format PDF & Word
- 💼 **Rekomendasi Lowongan** — AI mencocokkan CV dengan database 473+ lowongan kerja Indonesia via Qdrant Vector Search
- ✍️ **Review CV** — Analisis ATS score, feedback, dan generate CV ATS-friendly
- 💬 **Konsultasi Karir** — Chat dengan AI career consultant berbasis Gemini
- 🎤 **Mock Interview** — Simulasi wawancara kerja dengan AI interviewer

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI/LLM**: Google Gemini 2.5 Flash
- **Vector Store**: Qdrant Cloud (Semantic Search)
- **Database**: Aiven MySQL (SQLAlchemy)
- **Deployment**: Google Cloud Run (asia-southeast2)
- **Embeddings**: Gemini Embedding API

## 🚀 Deployment

Aplikasi di-deploy menggunakan Google Cloud Run:
```
Service: difi
Region: asia-southeast2 (Jakarta)
URL: https://difi-547610088942.asia-southeast2.run.app
```

## ⚙️ Setup Lokal

1. Clone repository ini
2. Copy `.env.example` menjadi `.env` dan isi dengan credentials Anda
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```

## 📋 Environment Variables

Lihat `.env.example` untuk daftar variabel yang diperlukan:
- `GEMINI_API_KEY` — Google Gemini API Key
- `DATABASE_URL` — Aiven MySQL connection string
- `QDRANT_URL` & `QDRANT_API_KEY` — Qdrant Cloud credentials
- `VECTOR_STORE` — `qdrant` atau `chromadb`
