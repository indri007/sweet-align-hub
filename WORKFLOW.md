# Technical Workflow Specification — JobMatch AI (V2.0)

**Document Type:** System Workflow & Data Pipeline Specification
**Author:** Principal Software Engineering Team (Antigravity)
**Date:** July 19, 2026

Dokumen ini memetakan *End-to-End User Journey* dan aliran data (*Data Flow*) di dalam sistem JobMatch AI V2.0. Proses direpresentasikan sebagai *pipeline* terstruktur dari titik masuk (*ingress*) hingga penyimpanan telemetri asinkron (*egress*).

---

### Phase 1: Identity & Access Management (IAM)
*   **Trigger:** Klien (*Browser*) melakukan GET request ke *endpoint* aplikasi.
*   **Proses:** Sistem memberlakukan *route guarding*. Pengguna diarahkan ke *OAuth 2.0 Authorization Code Flow* (via Google).
*   **Output:** Setelah *callback* berhasil divalidasi dengan `client_secret`, sistem menerbitkan *Session Cookie* tersandi (terenkripsi) dan menginisialisasi *State Object* spesifik untuk sesi pengguna tersebut di memori Streamlit.

### Phase 2: Data Ingestion & Pre-processing (Step A)
*   **Trigger:** *Upload* dokumen (PDF/DOCX) via antarmuka.
*   **Proses:** 
    *   **Extraction:** `cv_processor.py` melakukan *parsing* teks. Jika terdeteksi dokumen berbasis gambar, sistem akan melakukan *fallback* ke modul *Optical Character Recognition* (OCR) via Vision API.
    *   **Analysis:** *Payload* teks dikirim ke `cv_analyzer_agent.py` yang memanggil LLM (Groq/Gemini) untuk melakukan *Named Entity Recognition* (NER) guna mengekstrak *skill*, pengalaman, dan menghasilkan skor kelayakan (ATS Score).
*   **Output:** *Structured JSON/Dictionary* berisi entitas CV yang disimpan ke dalam *Session State*.

### Phase 3: Multi-modal Retrieval System (Step B)
*   **Trigger:** Permintaan rekomendasi lowongan atau *query* natural dari pengguna.
*   **Proses (Vector Retrieval - RAG):** 
    *   Teks CV diproses oleh model `gemini-embedding-001` menjadi vektor berdimensi tinggi.
    *   Sistem mengeksekusi *k-Nearest Neighbors (k-NN) search* via *Cosine Similarity* pada Qdrant Vector DB untuk mencari lowongan yang relevan secara semantik.
*   **Proses (Structured Retrieval - Text-to-SQL):** 
    *   Jika *intent* pengguna bersifat analitikal (contoh: "Gaji di atas 10 juta"), `sql_agent.py` menerjemahkan *Natural Language* menjadi kueri SQL.
    *   Sistem mengeksekusi *Read-Only Query* ke Aiven MySQL dan mengembalikan *Recordset*.
*   **Output:** Agregasi data lowongan (*Candidate Set*) yang ditampilkan ke *View Layer*.

### Phase 4: Content Generation & Optimization (Step C & D)
*   **Trigger:** Inisiasi pembuatan CV ATS atau sesi konsultasi.
*   **Proses (ATS Generator):** Menggunakan teknik *Prompt Engineering* (Few-shot prompting), AI merekonstruksi struktur *string* CV asli pengguna agar memiliki kepadatan *keyword* (Keyword Density) yang beririsan dengan *Job Description* dari Phase 3.
*   **Proses (Career Chat):** Chatbot menggunakan arsitektur *Retrieval-Augmented Chat* di mana riwayat percakapan (*Sliding Window Memory*), teks CV, dan konteks pekerjaan disuntikkan secara dinamis ke dalam *System Prompt* setiap kali LLM dipanggil.

### Phase 5: Stateful Interactive Simulation (Step E)
*   **Trigger:** Eksekusi modul *Mock Interview*.
*   **Proses:** Sistem menginisiasi *State Machine* sederhana. `interview_agent.py` bertindak sebagai *Agentic Loop*:
    1. Menggenerasi pertanyaan *behavioral/technical* berdasarkan kelemahan yang diekstrak pada Phase 2.
    2. Menunggu *input* asinkron dari pengguna.
    3. LLM mengevaluasi *input* berdasarkan rubrik penilaian (*Scoring Matrix*) dan menghasilkan *feedback*.
*   **Output:** Log evaluasi kuantitatif dan kualitatif.

### Phase 6: Asynchronous Telemetry & Event Sourcing (Background)
*   **Trigger:** Terjadi interaksi kritikal pada Phase 2, 3, 4, atau 5.
*   **Proses:** 
    *   Alih-alih melakukan pemblokiran (*Synchronous HTTP Call*), sistem memanggil `kafka_producer.py`.
    *   Data interaksi (*JSON payload*) diserialisasi dan di- *publish* ke Kafka *Topics* (`interview-logs`, `persona_logs`) pada *cluster* Aiven.
    *   Sistem menggunakan mekanisme *Fire-and-Forget* dengan *callback* ringan untuk *error handling*.
*   **Output:** Aliran data (*Data Stream*) yang persisten dan siap dikonsumsi (*consumed*) oleh *pipeline Analytics/ETL* di masa depan (*Data as an Asset*).
