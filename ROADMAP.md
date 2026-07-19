# Limitations & 1-Year Roadmap — JobMatch AI (V2.0)

**Document Type:** Strategic Technical Roadmap
**Author:** Principal Software Engineering Team (Antigravity)
**Date:** July 19, 2026

Dokumen ini memetakan batasan teknis (Technical Debt & Constraints) dari arsitektur JobMatch AI saat ini, serta visi pengembangan strategis untuk 12 bulan ke depan demi mencapai skala *Hyper-Growth*.

---

## A. Keterbatasan Arsitektur Saat Ini (Current Limitations)

Meskipun sistem telah menggunakan arsitektur *Enterprise*, masih terdapat beberapa hambatan struktural untuk melayani jutaan pengguna secara paralel (B2C Scale):

1. **Ketergantungan Eksternal (API Rate Limits & Latency):** 
   Sistem masih sangat bergantung pada *third-party API* (Groq, Gemini). Jika terjadi lonjakan lalu lintas ekstrem (*Spike Traffic*), kita berisiko terkena pemblokiran sementara (*Rate Limiting*) atau latensi tinggi dari sisi vendor, yang akan merusak *User Experience*.
2. **Keterbatasan Frontend (Streamlit Constraints):** 
   Streamlit sangat brilian untuk *Rapid Prototyping* dan visualisasi data. Namun, untuk aplikasi konsumen berbasis *Mobile-First*, arsitektur *Server-Side Rendering* milik Streamlit cukup berat, mengonsumsi banyak RAM (Stateful), dan sulit dioptimalkan untuk SEO (Search Engine Optimization).
3. **Pemrosesan Sinkron (*Synchronous Heavy-Lifting*):** 
   Saat ini, proses ekstraksi CV (OCR) dan pembuatan Vektor Embedding dilakukan secara *Real-Time* saat pengguna menunggu. Jika *file* PDF sangat besar, pengguna akan terjebak di layar *Loading*.
4. **Cold Starts:** 
   Karena di-host pada lingkungan *Serverless* (Streamlit Cloud / Cloud Run), aplikasi membutuhkan waktu beberapa detik untuk "pemanasan" (*Cold Start*) jika tidak ada yang mengaksesnya selama beberapa jam.

---

## B. Rencana Pengembangan Strategis (1-Year Roadmap)

Untuk bertransformasi dari proyek *Final Project* menjadi *Tech Startup* yang sesungguhnya (Unicorn Trajectory), berikut adalah peta jalan 1 tahun kita:

### Q1-Q2: Decoupling & Skalabilitas UI (Bulan 1-6)
*   **Headless Architecture:** Memisahkan logika AI dan *Database* sepenuhnya dari tampilan. Kita akan membangun **FastAPI / Go-lang Backend** murni.
*   **Modern Frontend Migration:** Mengganti Streamlit dengan kerangka kerja modern seperti **Next.js (React)** atau **Flutter** untuk menghasilkan aplikasi web/mobile yang sangat responsif, ringan, dan SEO-friendly.
*   **Asynchronous Task Queue:** Mengintegrasikan **Celery** atau **GCP Pub/Sub**. Saat pengguna mengunggah CV, mereka langsung masuk ke *Dashboard*, sementara ekstraksi AI dilakukan di latar belakang (*Background Job*).

### Q3: Model Proprietary & Optimalisasi Biaya (Bulan 7-9)
*   **Fine-Tuning In-House Models:** Berhenti menyewa "otak" orang lain. Kita akan men- *download* model *Open-Source* (seperti Llama 3 8B) dan melatihnya secara spesifik dengan jutaan data CV orang Indonesia. Model ini akan di- *host* secara mandiri pada infrastruktur GPU kita (misal: GCP Vertex AI), memangkas biaya API hingga 80%.
*   **Advanced RAG Caching:** Menerapkan *Semantic Cache* (Redis) agar AI tidak perlu berpikir ulang jika ada pengguna yang menanyakan hal yang persis sama.

### Q4: Monetisasi & Predictive Analytics (Bulan 10-12)
*   **Harvesting Kafka Data Lake:** Ini adalah masa panen. Data interaksi pelamar yang kita timbun di **Aiven Kafka** sejak V2.0 akan dianalisis. Kita akan membangun *Predictive AI* untuk memprediksi "Apakah kandidat ini akan *resign* dalam 6 bulan?" berdasarkan gaya wawancara mereka.
*   **B2B Recruiter Portal:** Mengembangkan sayap dari aplikasi pencari kerja (B2C) menjadi aplikasi B2B. Kita akan membuat *dashboard* berbayar khusus untuk HRD Perusahaan agar mereka bisa langsung memburu kandidat dengan skor ATS tertinggi di *database* kita (Two-Sided Marketplace).

---
*Visi ini mengakhiri fase purwarupa dan memulai fase komersialisasi produk secara masif.*
