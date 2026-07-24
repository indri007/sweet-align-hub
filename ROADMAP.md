# Technical Limitations & Strategic Roadmap — JobMatch AI (V2.0)

**Document Type:** Technical Constraints & 12-Month Development Strategy
**Author:** Principal Software Engineering Team (Antigravity)
**Date:** July 19, 2026

Dokumen ini memetakan batasan teknis (*Technical Debt & Constraints*) dari arsitektur JobMatch AI saat ini, serta visi pengembangan strategis perangkat lunak untuk 12 bulan ke depan guna mencapai skalabilitas level *Enterprise* (B2C & B2B Scale).

---

## A. Analisis Keterbatasan Sistem Berjalan (Current Technical Constraints)

Meskipun sistem telah mengadopsi arsitektur berbasis *microservices* dan *event-streaming*, masih terdapat beberapa *bottleneck* struktural:

1. **Vendor Lock-in & API Quota Constraints:** 
   Sistem masih memiliki ketergantungan yang tinggi pada *third-party LLM providers* (Groq, Gemini). Dalam skenario *high-concurrency traffic*, aplikasi rentan terhadap *rate-limiting* (429 Too Many Requests) dan fluktuasi latensi jaringan dari pihak ketiga, yang berpotensi mendegradasi *Service Level Agreement* (SLA).
2. **Keterbatasan Arsitektur Stateful UI (Streamlit):** 
   Streamlit menggunakan arsitektur *Server-Side Rendering* (SSR) dengan manajemen sesi yang *stateful* (memori-intensif). Pendekatan ini suboptimal untuk aplikasi B2C berskala besar yang menuntut optimasi SEO (*Search Engine Optimization*) dan responsivitas *Mobile-First*.
3. **Synchronous Processing Bottlenecks:** 
   Alur kerja saat ini (seperti eksekusi OCR dokumen PDF dan pembuatan vektor *embeddings*) diproses secara *synchronous* pada *Thread* utama. Hal ini menyebabkan *blocking* pada antarmuka pengguna (UI) selama proses komputasi berlangsung.
4. **Cold Start Latency:** 
   Infrastruktur *Serverless* saat ini menimbulkan latensi inisialisasi (*Cold Start*) apabila kontainer aplikasi diaktifkan kembali dari fase *idle*, sehingga waktu tanggap awal (Time-to-First-Byte) tidak optimal.

---

## B. Peta Jalan Pengembangan Strategis (12-Month Strategic Roadmap)

Untuk mengatasi keterbatasan di atas, pengembangan perangkat lunak akan difokuskan pada pemisahan arsitektur (*Decoupling*) dan internalisasi model AI.

### Tahap 1: Decoupling & Asynchronous Optimization (Q1 - Q2)
*   **Headless Backend Migration:** Melakukan *refactoring* dengan memisahkan *Business Logic Layer* dan *Data Access Layer* dari UI, membungkusnya dalam kerangka kerja **FastAPI** (Python) atau Go-lang untuk mencapai arsitektur berbasis RESTful/GraphQL murni.
*   **Modern Frontend Implementation:** Mengganti *View Layer* berbasis Streamlit dengan kerangka kerja modern berbasis komponen seperti **Next.js (React)** atau **Flutter** untuk mengoptimalkan efisiensi rendering (Client-Side Rendering) dan SEO.
*   **Message Brokers & Worker Queues:** Mengimplementasikan **Celery** (didukung oleh Redis/RabbitMQ) untuk menangani tugas berat (*heavy I/O bindings*) secara asinkron (misalnya: *parsing* CV dan *vector ingestion*), sehingga latensi UI dapat ditekan mendekati nol.

### Tahap 2: Proprietary LLM Deployment & Cost Efficiency (Q3)
*   **In-House Model Fine-Tuning:** Membangun kemandirian infrastruktur AI dengan melatih ulang (*Fine-tuning*) model LLM *Open-Weights* (contoh: LLaMA 3) menggunakan Dataset spesifik industri HR Indonesia. Model proprietary ini akan di- *deploy* ke infrastruktur GPU privat terdedikasi (misal: GCP Vertex AI endpoints), memangkas *Operational Expenditure* (OpEx) dari penggunaan API pihak ketiga.
*   **Semantic Caching Layer:** Mengimplementasikan *Semantic Cache* menggunakan Redis Vector Search untuk merespons kueri berulang (redundant) tanpa harus memanggil proses inferensi LLM (*LLM Inference bypass*).

### Tahap 3: Predictive Analytics & B2B Ecosystem Expansion (Q4)
*   **Kafka Data Lake Harvesting:** Mengonsumsi (*Consume*) aliran telemetri asinkron dari **Aiven Kafka** yang telah terakumulasi, lalu mentransformasikannya melalui *pipeline ETL*. Data ini akan digunakan untuk melatih model *Machine Learning* prediktif (contoh: *Employee Retention Prediction* atau *Success Rate Forecasting*).
*   **Two-Sided Marketplace (B2B/B2C):** Mengekspansi arsitektur sistem untuk mendukung *Multi-Tenant RBAC* (Role-Based Access Control). Hal ini memungkinkan pembuatan portal khusus *Recruiter* (B2B), di mana pihak korporasi dapat melakukan *query* langsung terhadap *pool* kandidat ber-skor ATS tertinggi di *database* secara terotorisasi.
