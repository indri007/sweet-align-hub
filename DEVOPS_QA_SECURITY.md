# Quality Assurance, Security, & DevOps Specification — JobMatch AI (V2.0)

**Document Type:** Technical Engineering Pillars (Testing, Pentesting, DevOps)
**Author:** Principal Software Engineering Team (Antigravity)
**Date:** July 19, 2026

Dokumen ini mendeskripsikan 3 pilar validasi teknis (*Engineering Pillars*) yang menopang arsitektur JobMatch AI agar siap dioperasikan pada level *Enterprise* (Production-Ready). 

---

## 1. Automated Testing & Quality Assurance (QA)

Dalam ekosistem Generative AI, pengujian tidak terbatas pada fungsi deterministik, melainkan evaluasi probabilistik terhadap *output* LLM.
*   **AI Evaluation Framework (RAGAS):** Terdapat di dalam modul `evaluation/` (`run_ragas_eval.py`). Sistem secara periodik mengukur tingkat akurasi model AI melalui metrik matematis:
    *   *Faithfulness* (Mendeteksi halusinasi data).
    *   *Answer Relevance* (Relevansi terhadap *query*).
    *   *Context Precision* (Ketepatan pengambilan vektor lowongan).
*   **System Liveness Probes:** Skrip `health_check.py` bertindak sebagai *watchdog* untuk memantau status kesehatan *endpoints* secara terus-menerus (Gemini, Groq, Qdrant, Aiven).

---

## 2. DevSecOps & Security Defenses (Pentesting Baseline)

Sistem telah dirancang dengan mengedepankan postur *Zero-Trust* dan perlindungan terhadap kerentanan (*vulnerabilities*) standar industri (OWASP Top 10):
*   **Injeksi SQL Terisolasi (SQL Injection Prevention):** Modul `sql_agent.py` mengeksekusi konversi Text-to-SQL menggunakan mekanisme **SQLAlchemy ORM**. Proses ini melakukan sanitasi input dan pengikatan parameter (*Parameter Binding*), menetralkan potensi injeksi manipulatif (seperti `DROP TABLE` atau `UNION SELECT`).
*   **Data in Transit Encryption (TLS/SSL):** Koneksi eksternal ke Aiven MySQL dan Aiven Kafka diamankan melalui skema *Mutual TLS* menggunakan sertifikat `ca.pem`. Hal ini mencegah celah penyadapan *Man-in-the-Middle (MITM) attack* pada jaringan tidak aman.
*   **Secret Management:** Tidak ada kredensial (*API Keys*, kata sandi) yang tertanam statis (hardcoded) di dalam *source code*. Semua rahasia dikelola secara eksternal via `.env` atau `secrets.toml` di Cloud, yang diproteksi oleh `.gitignore`.
*   **Identity Provider:** Otentikasi sesi di-offload ke *Google OAuth 2.0* terverifikasi, meminimalisir risiko kebocoran kata sandi lokal.

---

## 3. DevOps & Continuous Integration/Continuous Deployment (CI/CD)

Pengiriman kode dilakukan secara otomatis (*Automated Pipeline*) untuk meminimalkan intervensi manual (Human Error).
*   **Immutable Infrastructure:** Terdapat `Dockerfile` berbasis `python:3.10-slim`. Ini menjamin konsistensi *Environment* sehingga aplikasi yang berjalan di Streamlit Cloud memiliki dependensi yang absolut sama (1:1) dengan konfigurasi laptop pengembang (*Developer Localhost*).
*   **GitHub Actions CI Pipeline:** *Trigger* otomatis tersedia di dalam direktori `.github/workflows/` (`ci.yml`, `daily-job-fetch.yml`). *Pipeline* ini bertanggung jawab untuk mengeksekusi integrasi *linting*, pengujian keamanan, dan tugas pengambilan data sinkronisasi lowongan kerja (*Cron Jobs*).
*   **Continuous Deployment:** Integrasi *hook* langsung antara GitHub *branch* `streamlit` dengan layanan Streamlit Cloud. Setiap kali terjadi *Push*, platform Cloud akan merobohkan kontainer lama dan membangun kontainer baru (*Rolling Update*) tanpa *downtime* yang masif.

---
*Dokumen ini merupakan standar operasional prosedur untuk menjaga stabilitas, keamanan, dan pengiriman (delivery) JobMatch AI.*
