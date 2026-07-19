# Architecture Review — JobMatch AI (V2.0)

**Document Type:** Technical Architecture Review (TAR)
**Author:** Principal Software Engineering Team (Antigravity)
**Date:** July 19, 2026

Sistem **JobMatch AI (V2.0)** ini mengadopsi pendekatan **Distributed Microservices** yang dipadukan dengan **Event-Driven Architecture (EDA)**. Tujuan utama dari desain ini adalah mencapai *high availability*, *scalability*, dan *loose coupling* di antara komponen AI dan persistensi data.

Berikut adalah *Architectural Review* dari sistem yang telah dibangun:

---

## 1. Presentation & Auth Layer (Decoupled UI)
*   **Komponen:** Streamlit di-host pada *Platform-as-a-Service* (Streamlit Cloud).
*   **Mekanisme:** *Layer* ini bertindak murni sebagai *dumb terminal* (hanya menangani UI/UX dan manajemen *state* sessional). Pemrosesan berat tidak terjadi di sini. 
*   **Security:** Menggunakan *native Google OAuth 2.0 flow* dengan *stateless JWT/Session cookies*. Sertifikat TLS/SSL *end-to-end* diaplikasikan untuk melindungi *payload* data sensitif pelamar.
*   **CI/CD Pipeline:** Terintegrasi secara *Continuous Deployment* dengan *branch* `streamlit` di GitHub. Setiap *commit* akan secara otomatis memicu fasa *build* dan *dependency resolution* (`requirements.txt`) tanpa *downtime* yang signifikan.

---

## 2. Cognitive & Routing Layer (Multi-LLM Adapter Pattern)
Mengingat latensi dan *rate-limiting* adalah *bottleneck* utama dalam aplikasi GenAI, kita mengimplementasikan **Strategy/Adapter Pattern** pada modul `llm_client.py`:
*   **Dynamic LLM Routing:** Permintaan dari UI tidak di-hardcode ke satu vendor. Melalui abstraksi OpenAI-compatible SDK, sistem akan melakukan *routing* ke **Groq (Llama-3.3)** untuk inferensi latensi rendah (sangat kritikal untuk *streaming chat*), sementara **Google Gemini** diisolasi khusus untuk beban *multimodal* dan ekstraksi *Document/OCR*.
*   **Fault Tolerance:** Terdapat mekanisme *fallback* ke OpenRouter atau Mistral untuk menjamin sistem tetap beroperasi (SLA 99.9%) apabila *endpoint* primer mengalami *degraded performance* (RTO/Timeout).

---

## 3. Persistence & Retrieval Layer (Hybrid Dual-Cluster)
Sistem memisahkan beban operasional secara arsitektural menjadi dua kluster terpisah untuk menjaga isolasi data operasional vs memori agen:
*   **Relational Database (Aiven 1 - Primary SQL):** Bertindak sebagai *System of Record* (SoR) untuk data terstruktur lowongan kerja dan profil pelamar. Terhubung via *SQLAlchemy ORM* menggunakan koneksi aman `ca.pem` (*Mutual TLS*).
*   **Vector Database (Qdrant 1 - Primary Cloud):** Mengadopsi arsitektur **Retrieval-Augmented Generation (RAG)** untuk pencocokan (*matching*) CV pelamar dengan basis data lowongan (*Jobs*) dan pengetahuan HR.
*   **Vector Database (Qdrant 2 - Secondary CS Cloud):** Diisolasi secara khusus untuk menampung *Knowledge Base* (Pengetahuan) dan *Long-Term Memory* (Memori Jangka Panjang) dari agen *Customer Service* kita, yaitu **Agen Veronika** dan **Agen Leonardo**. Hal ini mencegah kontaminasi pencarian (*search contamination*) antara data HR dan percakapan pelanggan.

---

## 4. Telemetry & Asynchronous Event Streaming (Kafka - Aiven 2)
Untuk memenuhi standar *Enterprise Data-as-an-Asset*, sistem mengintegrasikan **Apache Kafka (Aiven 2 - Secondary Cluster)** menggunakan *library* `confluent-kafka` (C-based wrapper untuk performa I/O tinggi):
*   **Fire-and-Forget Telemetry:** Log interaksi, *scoring* CV, dan percakapan (memori) dari **Veronika** dan **Leonardo** dilemparkan ke *message broker* (Kafka Topics: `interview-logs`, `persona_logs`, `cs-memory-stream`) secara *asynchronous*.
*   Mekanisme *Data Stream* pada **Aiven 2** ini memastikan proses *logging* sejarah obrolan Veronika dan Leonardo tidak memblokir *Thread* utama aplikasi (*non-blocking I/O*). Seluruh sejarah *knowledge* ini dipersistenkan (*persisted*) agar agen-agen ini dapat "belajar dari sejarah (*history*)" untuk menjadi lebih baik (seperti sistem agen cerdas modern).

---

## 5. Orchestration Layer (N8N Dual-Engine)
Untuk memenuhi *use case* otomasi B2B, sistem mendukung *toggleable architecture*:
*   **Choreography (Python Direct):** *Default mode* di mana kode *Python* mengeksekusi semua *chain* agen secara linear untuk latensi serendah mungkin.
*   **Orchestration (N8N Webhook):** Tersedia *endpoint* HTTP via `n8n_client.py`. Jika variabel `USE_N8N` di-inject via env var, aplikasi akan bertindak sebagai *trigger* (Event Publisher) yang mengirimkan HTTP POST *payload* ke N8N. N8N kemudian mengambil alih *State Machine* dari alur AI (*LangChain nodes*) untuk diintegrasikan dengan servis pihak ketiga (Email, CRM, dll).

---

**Kesimpulan Audit:**
Arsitektur ini sangat *cloud-native*, persisten, dan *loosely coupled*. Secara *engineering*, *codebase* kita siap menahan lonjakan *traffic* (skalabilitas vertikal via API *providers*, dan skalabilitas horizontal via *stateless Streamlit containers*) tanpa adanya poin kegagalan tunggal (*Single Point of Failure*).
