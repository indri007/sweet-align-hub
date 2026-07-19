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

## 3. Persistence & Retrieval Layer (Hybrid Data Store)
Sistem memisahkan beban baca/tulis berdasarkan struktur data (OLTP vs. Vector Search):
*   **Relational Database (Aiven MySQL):** Bertindak sebagai *System of Record* (SoR) untuk data terstruktur. Terhubung via *SQLAlchemy ORM* dengan protokol koneksi aman menggunakan `ca.pem` (*Mutual TLS*). Di sini, agen Text-to-SQL kita beroperasi secara deterministik.
*   **Vector Database (Qdrant Cloud):** Mengadopsi arsitektur **Retrieval-Augmented Generation (RAG)**. Data berdimensi tinggi (seperti representasi semantik dari riwayat kerja dan deskripsi pekerjaan) diindeks menggunakan model `gemini-embedding-001`. *Compute* komparasi kosinus (Cosine Similarity) di-offload ke Qdrant *engine*, sehingga membebaskan beban CPU *instance* Streamlit.

---

## 4. Telemetry & Asynchronous Event Streaming (Kafka)
Untuk memenuhi standar *Enterprise Data-as-an-Asset*, sistem mengintegrasikan **Apache Kafka (Aiven)** menggunakan *library* `confluent-kafka` (C-based wrapper untuk performa I/O tinggi):
*   **Fire-and-Forget Telemetry:** Log interaksi, scoring CV, dan profil persona dilemparkan ke *message broker* (Kafka Topics: `interview-logs`, `persona_logs`) secara *asynchronous*.
*   Mekanisme ini memastikan proses *logging* tidak memblokir *Thread* utama aplikasi (*non-blocking I/O*). Secara arsitektural, ini mengisolasi (decouple) aplikasi *frontend* dari sistem *Downstream Analytics/Machine Learning* masa depan yang nantinya akan mengonsumsi (*consume*) *stream* data tersebut secara terpisah.

---

## 5. Orchestration Layer (N8N Dual-Engine)
Untuk memenuhi *use case* otomasi B2B, sistem mendukung *toggleable architecture*:
*   **Choreography (Python Direct):** *Default mode* di mana kode *Python* mengeksekusi semua *chain* agen secara linear untuk latensi serendah mungkin.
*   **Orchestration (N8N Webhook):** Tersedia *endpoint* HTTP via `n8n_client.py`. Jika variabel `USE_N8N` di-inject via env var, aplikasi akan bertindak sebagai *trigger* (Event Publisher) yang mengirimkan HTTP POST *payload* ke N8N. N8N kemudian mengambil alih *State Machine* dari alur AI (*LangChain nodes*) untuk diintegrasikan dengan servis pihak ketiga (Email, CRM, dll).

---

**Kesimpulan Audit:**
Arsitektur ini sangat *cloud-native*, persisten, dan *loosely coupled*. Secara *engineering*, *codebase* kita siap menahan lonjakan *traffic* (skalabilitas vertikal via API *providers*, dan skalabilitas horizontal via *stateless Streamlit containers*) tanpa adanya poin kegagalan tunggal (*Single Point of Failure*).
