# PRD: JobMatch AI — Platform Scoring CV & Job Matching Berbasis Multi-Agent

**Versi:** 3.0 (Final — konsolidasi lengkap, termasuk arsitektur target)
**Nama project:** JobMatch AI *(sebelumnya disebut "sweet-align-hub" — nama folder lokal lama, sudah tidak dipakai lagi mulai versi ini)*
**Live app:** `jobsmatch.streamlit.app`
**Disusun oleh:** Claude, berdasarkan data Google Drive (Knowledge Base, brief JCAI, rubrik penilaian, workflow n8n V3 & V4, 6 workflow terpisah), file yang di-upload, dan screenshot kondisi app langsung
**Tanggal:** 21 Juli 2026
**Status:** ✅ **Disetujui** — jadi acuan resmi untuk eksekusi selanjutnya. Dokumen ini menggabungkan seluruh audit (§2), spesifikasi fitur (§11), dan arsitektur target (§7B) dalam satu versi final. Pertanyaan terbuka di §13 tetap perlu keputusan sebelum item terkait dikerjakan.

---

## Ringkasan Eksekutif

JobMatch AI **sudah live dan sebagian besar fiturnya berfungsi**. Ini bukan lagi tahap rencana — ini dokumentasi & rencana perbaikan atas sistem yang sudah berjalan.

| Aspek | Status |
|---|---|
| Infrastruktur (Gemini, Qdrant, MySQL/Aiven, N8N) | ✅ Semua confirmed hidup (System Status panel, 21 Juli 16:34) |
| Multi-agent system di N8N | ✅ Jalan — Dual-Pipeline: N8N (V4) untuk fitur linear, Python-Native untuk stateful (§2.6) |
| Upload CV → 10 lowongan match dengan skor | ✅ Jalan |
| 3 mode pencarian lowongan (Dataset/Internet/Scrape Live) | ✅ Jalan |
| Fitur "Analisis AI" (AI Summary) | ✅ **Fixed di kode lokal** — tinggal `git commit`+`push` untuk deploy (§2.5). ⚠️ Tapi ada klaim "OpenAI fallback" yang perlu diklarifikasi dulu sebelum push |
| **Generate CV ATS-optimized (ID & EN)** | ⚠️ Workflow-nya ada (`3 - ATS CV Generator`) tapi kemungkinan **legacy/tidak dipanggil live** (§2.7) — perlu verifikasi |
| **Family workflow terpisah (1-6)** | ✅ **Dikonfirmasi legacy**, app live cuma pakai V4 — aman dibersihkan setelah 1x verifikasi (§2.7) |
| Workflow n8n V4 | ⚠️ Masih ada node rusak/yatim yang perlu dibersihkan (§2.5A) |
| Agent Leonardo (HRD) & Veronika (CS) | ⚠️ Belum dipisah datanya, tapi **dikonfirmasi non-blocking** — boleh ditunda (§2.8) |
| Struktur agent vs brief resmi (3 agent literal) | ⚠️ Perlu diklarifikasi ke mentor — implementasi sekarang beda pola |

**Yang paling mendesak sekarang:** (1) klarifikasi soal OpenAI fallback sebelum deploy, (2) kalau sudah jelas cuma Gemini, langsung `git commit`+`push` untuk hilangkan bug Groq. Sisanya (family workflow, Leonardo/Veronika) sudah dikonfirmasi tidak mendesak.

---

## 1. Konteks Project

### 1.1 Ini adalah Final Project JCAI Purwadhika
JobMatch AI adalah **Final Project program Job Connector AI Engineering (JCAI), Purwadhika Digital Technology School, angkatan 2025**, dikerjakan berkelompok (2-3 peserta). Brief resmi (`[JCAI - 2025] Final Project - N8N Version.docx`) dan rubrik penilaian (`Rubrik Penilaian Final Project JCAI.docx`) ditemukan di Google Drive.

**Fakta kunci dari brief:**
- Brief menyediakan 2 dataset resmi: **Olist Dataset** (e-commerce Brasil) dan **Indonesian Job Dataset**. **Olist Dataset adalah tugas kelompok lain** — kelompok JobMatch AI mendapat pembagian **Job Dataset saja**. Dataset Job ini **persis sama** dengan `jobs__1__jsonl.xlsx` yang kamu upload (kolom identik: job_title, company_name, location, work_type, salary, job_description, _scrape_timestamp).
- **Linimasa resmi brief: 27 November 2025 – 6 Januari 2026** — sudah lewat dari hari ini (21 Juli 2026). Status ini perlu dikonfirmasi ke pihak Purwadhika (lihat §13).
- Wajib pakai **arsitektur multi-agent minimal 3 komponen** (Agent Utama, Agent RAG, Agent SQL).
- **N8N wajib di-deploy sebagai REST API** (node Webhook, workflow ON/Publish) — Streamlit memanggil endpoint ini, bukan connect langsung ke Gemini/Qdrant/Aiven.
- Requirement Advance/Nice-to-Have resmi: **upload CV → rekomendasi lowongan cocok**, dan **career consultation** — konfirmasi bahwa fitur inti JobMatch AI memang sesuai kriteria nilai tambah brief.

### 1.2 Masalah yang Dihadapi Job Seeker
- Tidak tahu apakah CV lolos ATS sebelum sampai ke HRD.
- Tidak tahu bagian mana dari CV yang perlu diperbaiki secara konkret.
- Tidak tahu lowongan mana yang benar-benar cocok — hanya mengandalkan pencarian keyword manual.
- CV dalam 1 bahasa saja, padahal lowongan butuh versi ID & EN.

### 1.3 Aset yang Dimiliki
1. **HRD Toolkit** (Google Drive "data hrd", ZIP 1: 170 file) — rubrik penilaian, kamus kompetensi, instrumen assessment center, SOP rekrutmen, dari praktisi HRD 25 tahun pengalaman.
2. **Job Database** — 473 lowongan kerja riil (scraping per 24 November 2025).

Kedua sumber digabung jadi **Knowledge Base** (`ATS_CV_Knowledge_Base_lengkap.xlsx`, 16 sheet).

---

## 2. Kondisi Nyata Sistem Saat Ini (per 21 Juli 2026)

### 2.1 Sumber Kebenaran

Bagian ini disusun dari 4 sumber yang saling dicek silang:
1. **File workflow n8n V3** — `JobMatch AI V3 (Ultimate Enterprise Architecture).json`, ditemukan di Drive
2. **Screenshot workflow n8n V4 "Fixed & Simplified"** — langsung dari editor n8n (`n8n.kelasantai.online`, 21 Juli 17:08), versi lebih baru dari file V3 di atas
3. **Struktur folder project** — dari laporan Antigravity atas isi `/Users/jevin/Downloads/sweet-align-hub-main` (nama folder lokal lama)
4. **Screenshot app live** — `jobsmatch.streamlit.app`, 3 screenshot (halaman hasil match, halaman "Cari di Internet", halaman "Scrape Lowongan Live" + System Status)

> **Catatan versi:** temuan di §2.2–§2.5 awalnya dari file V3. §2.5A menandai apa yang sudah diperbaiki di V4 dan apa yang masih sama.

### 2.2 Arsitektur Agent yang Sesungguhnya

Sistem SQL Agent yang tadinya dikira "hilang" (file `sql_agent.py` ada di folder `_archive/` project Streamlit) ternyata **bukan hilang** — logic-nya dipindah dan diimplementasikan langsung di n8n sebagai **tool** di dalam satu AI Agent, bukan sebagai agent Python terpisah.

**Pola nyata:** 1 AI Agent (`toolsAgent`, LangChain) dengan 2 tool:
- `Vector Store Tool` → Qdrant, collection `indonesian_jobs_gemini`
- `Execute a SQL query in MySQL` → Aiven MySQL, tabel `jobs`

⚠️ **Catatan risiko akademik:** brief JCAI minta "setidaknya 3 komponen agent" secara literal. Pola "1 agent + 2 tools" ini **secara fungsi memenuhi** requirement (bisa jawab dari vectorDB *dan* SQL), tapi secara struktur bukan 3 agent terpisah. Perlu dikonfirmasi ke mentor apakah ini dianggap cukup (§13).

### 2.3 Skema Data Aktual (bukan asumsi)

- **Database:** Aiven **MySQL** (bukan PostgreSQL seperti draft awal saya).
- **Tabel `jobs`:** `job_title, company_name, location, work_type, salary_min (FLOAT), salary_max (FLOAT), job_description` — gaji dipisah jadi 2 kolom angka, bukan 1 kolom teks.
- **Collection Qdrant (Job Search):** `indonesian_jobs_gemini` — nama ini sempat berubah dari `indonesian_jobs_n8n` (V3) jadi `indonesian_jobs_gemini` (V4), **pastikan data yang sudah pernah di-embed dengan nama lama tidak "hilang"/perlu di-reindex ulang ke collection baru**.
- **Collection Qdrant (CS Memory):** `cs_memory` — dipakai bersama Veronika & Leonardo.
- **Kredensial n8n — HANYA Gemini yang dipakai untuk AI**, konsisten dengan penamaan `[nama layanan] cvatsjob`:
  - `Gemini cvatsjob` (AI — embedding & chat)
  - `Qdrant cvatsjob` (vector store)
  - `MySQL cvatsjob` (relational store)
  - **Tidak ada kredensial Groq/Cerebras/Zhipu di n8n manapun** (V3 maupun V4) — jejak provider lain itu murni sisa di `llm_client.py` sisi Streamlit yang jadi sumber bug §2.5. Untuk pengembangan selanjutnya, **anggap Gemini satu-satunya AI provider yang relevan**, provider lain tidak perlu dipikirkan lagi.
- **Model generatif:** `gemini-2.5-flash` — sekarang eksplisit tertulis di node `Gemini Chat Model` (V4), tidak lagi mengandalkan default seperti V3.
- **Izin akses database dipisah dengan baik:** `Aiven 1 (Primary SQL - Read Only)` cuma boleh SELECT (untuk cari data lowongan), `Aiven 2 (Telemetry Log Only)` cuma boleh INSERT (untuk simpan log percakapan) — praktik keamanan yang benar, tidak perlu diubah.

### 2.4 Fitur yang Sudah Live (dari screenshot langsung)

**3 mode pencarian lowongan:**
| Mode | Cara kerja |
|---|---|
| Dari Dataset (AI Match) | AI matching sungguhan ke `indonesian_jobs_gemini`, skor % + detail per lowongan |
| Cari di Internet | *Bukan AI search* — extract 1 keyword dari CV, generate link pencarian siap-klik ke LinkedIn/JobStreet/Google Jobs |
| Scrape Lowongan Live | Selenium + BeautifulSoup, scrape dinamis berdasarkan keyword & jumlah input user, hasil **otomatis masuk ke MySQL + ter-index ke Qdrant** secara real-time |

**Alur 5 step di Streamlit:** Upload CV → Cari Loker → Review → Konsultasi Karir → Mock Interview (dengan progress tracker).

**System Status (live check dari app):**
| Komponen | Status | Response time |
|---|---|---|
| Gemini API | OK | 33.8ms |
| Qdrant DB | OK | 569.7ms |
| MySQL DB (Aiven) | OK | 2419.0ms *(agak lambat, worth dicek)* |
| N8N | Active | - |

### 2.5 Yang Perlu Diperbaiki

**🚨 P0 — Bug aktif di production:** Fitur "Analisis AI" gagal dengan error:
```
model llama3-70b-8192 has been decommissioned and is no longer supported
```
Kode masih memanggil **Groq** untuk generate AI summary, padahal sudah diputuskan konsolidasi ke Gemini. Karena 3 komponen inti lain (Gemini, Qdrant, MySQL) confirmed sehat, bug ini **kemungkinan besar terisolasi di satu jalur kode saja** (kemungkinan `llm_client.py` sisi Streamlit yang belum ikut dimigrasikan ke Gemini, berbeda dari workflow n8n yang sudah 100% Gemini).

> **Update 21 Juli (dilaporkan Antigravity, belum diverifikasi independen):** `llm_client.py` di repo lokal **sudah dibersihkan dari Groq** — tinggal `git commit` + `git push` supaya Streamlit Cloud reload kode terbaru, bug akan hilang setelah deploy.
>
> **⚠️ Tapi ada 1 hal yang perlu diklarifikasi dulu sebelum push:** Antigravity melaporkan kode sekarang pakai **"Gemini sebagai model utama, OpenAI sebagai fallback"**. Ini **bertentangan** dengan keputusan konsolidasi Gemini-only sebelumnya (instruksi eksplisit: "hilangkan API key selain Gemini"). **Jangan langsung deploy sebelum ini diklarifikasi** — kalau OpenAI fallback ini tidak disengaja, sebaiknya dihapus juga sebelum push, supaya tidak keluar dari prinsip 1-provider yang sudah disepakati.

**⚠️ Masalah di file workflow n8n** (`JobMatch AI V3.json`), perlu dibersihkan sebelum demo/submit:

| Masalah | Detail |
|---|---|
| 🐛 2 Webhook path sama persis | Node `Webhook` dan `Streamlit App (Webhook Entry)` sama-sama pakai path `job-assistant` — berpotensi bentrok |
| 🐛 Node rusak | `Google Auth Validator` bertipe HTTP Request tapi diberi kredensial MySQL — tidak nyambung |
| 🧟 Node "yatim" | `Main Orchestrator Agent`, `HR Knowledge Tool`, `Qdrant 1 (Jobs Vector DB)`, `Aiven 1 (Primary SQL)` — draft awal yang ditinggal, tidak tersambung trigger apa pun |
| 🧟 Subsistem belum tersambung | `Veronika`/`Leonardo (CS Agent)` + collection `cs_memory` + tabel log `Aiven 2 (Telemetry/Kafka)` — sudah dibangun lengkap tapi tidak ada jalur dari Webhook ke sini, belum bisa dipanggil dari Streamlit |

### 2.5A Status Perbaikan V3 → V4 (update 21 Juli 17:08)

Workflow n8n sudah naik versi jadi **"JobMatch AI V4 (Fixed & Simplified)"**. Sebagian besar masalah struktural di §2.5 **sudah diperbaiki**:

| Masalah di V3 | Status di V4 |
|---|---|
| Node yatim (Main Orchestrator, Veronika, Leonardo tidak tersambung trigger) | ✅ **Fixed** — ada node baru **"Request Router"** (mode: Rules) yang menyambungkan Webhook ke 3 agent (Veronika/Leonardo/Main Orchestrator) berdasarkan aturan routing |
| 2 Webhook path sama persis | ✅ Fixed — sekarang cuma 1 "Streamlit App (Webhook Entry)" |
| Node rusak `Google Auth Validator` | ⚠️ **Diganti rencana** dengan Header Auth standar n8n — sudah ada instruksi di catatan node webhook, tapi **kredensialnya perlu dibuat manual** di n8n Settings > Credentials setelah import, belum otomatis jadi |
| 2 node Gemini Chat Model terpisah | ✅ Disederhanakan jadi **1 node** dipakai bersama oleh Main Orchestrator, Veronika, dan Leonardo |

**Yang MASIH SAMA (belum diperbaiki, perlu tindakan lanjutan):**
- `HR Knowledge Tool` masih terhubung ke `Qdrant 1 (Jobs Vector DB)` — deskripsi tool-nya sendiri eksplisit bilang "Cari informasi pekerjaan (job_title, company_name, job_description)", jadi memang murni tool pencarian lowongan yang salah nama, bukan tool HRD.
- Node **Leonardo masih literally berlabel "Leonardo (CS Agent)"** di kanvas n8n — belum diubah jadi peran HRD sama sekali, baik nama maupun datanya.
- Leonardo dan Veronika **masih berbagi sumber data yang sama**: keduanya terhubung ke `CS Knowledge Tool` → `Qdrant 2 (CS Memory DB)`, dan ke `Aiven 2 (Telemetry - Log Only)` yang sama.
- **Baru ditemukan:** kedua node agent (Veronika & Leonardo) **sama sekali tidak punya `systemMessage`** — beda dengan Main Orchestrator Agent yang sudah punya system prompt jelas ("Kamu adalah asisten pencari kerja..."). Artinya secara kepribadian/gaya jawab, Veronika dan Leonardo saat ini benar-benar identik, tidak cuma soal data.

**Kesimpulan:** perbaikan V4 fokus ke *pipa/wiring* (routing, konsolidasi model, keamanan akses DB) — bagus dan sudah selesai. Tapi **pemisahan peran Leonardo=HRD (§2.8) masih PR murni**, mencakup 3 hal: nama node, data source, DAN system prompt.

### 2.5B Bug Baru Ditemukan & Fixed: Mock Interview "Freeze" UI (dilaporkan Antigravity, 21 Juli)

**Gejala:** Saat user ketik jawaban di Mock Interview lalu Enter, tampilan terlihat seperti "tidak merespons"/freeze.

**Akar masalah (dilaporkan Antigravity):** Bukan agent yang mati — ada error di backend LLM (dugaan: rate limit Gemini, koneksi, atau format JSON tidak sesuai), tapi `pages/step_e_interview.py` langsung memanggil `st.rerun()` setelah error, jadi pesan error **kehapus dalam sepersekian detik sebelum sempat terbaca** — kelihatan seperti nge-freeze padahal sebenarnya ada error yang tidak sempat kelihatan.

**Fix yang dilaporkan sudah dikerjakan & di-commit:** Error sekarang ikut dicetak ke riwayat chat interview (ditandai ⚠️), tidak lagi terhapus otomatis oleh rerun. Status: **committed di lokal, belum di-push** — masuk antrean yang sama dengan fix bug Groq (§2.5) untuk dideploy bareng.

**⚠️ Belum jelas / perlu ditanya ke Antigravity:** disebutkan juga ada perbaikan di `vector_store.py` ("vector_store.py yang kita perbaiki tadi") tapi **belum ada detail apa yang diperbaiki di situ**. Ini perlu diklarifikasi sebelum push — jangan asumsikan itu perbaikan kecil/aman tanpa tahu isinya, karena `vector_store.py` menyentuh koneksi Qdrant yang dipakai hampir semua fitur RAG.

### 2.6 Arsitektur "Dual-Pipeline" (dilaporkan Antigravity, 21 Juli — belum diverifikasi independen)



> ⚠️ **Sumber:** ini laporan dari Antigravity (asisten coding kamu), berdasarkan `pre_redeploy_check.sh` dan isi `.env`/folder `agents/` di project. Saya belum baca langsung file-file itu — beda dengan temuan §2.1-§2.5 yang saya baca sendiri dari file JSON. Kalau ada waktu, ada baiknya diverifikasi silang (misal minta Antigravity tunjukkan isi `llm_client.py` atau `.env` — tanpa API key aslinya tentu saja).

Menjawab pertanyaan lama soal "6 endpoint terpisah vs workflow V4 — mana yang aktif" (§13 #7 versi lama): jawabannya **bukan salah satu, tapi dua pipeline yang sengaja jalan berdampingan**, dikontrol lewat `.env` (`USE_N8N=true/false`):

| Pipeline | Cara kerja | Dipakai untuk fitur apa | Kenapa |
|---|---|---|---|
| **1. Python-Native** | Streamlit → `agents/*.py` (`interview_agent.py`, `cv_analyzer_agent.py`, dst) → `llm_client.py` → Gemini/OpenAI langsung | Mock Interview, CS chat — fitur **stateful/multi-turn** | Kontrol penuh atas state percakapan + guardrail anti-halusinasi lebih stabil di Python murni |
| **2. N8N Orchestration** | Streamlit → webhook (`N8N_WEBHOOK_URL`) → workflow n8n (V4 dan/atau 6 endpoint) | Job matching/RAG — fitur **linear, stateless** | Low-code, gampang dimodif visual, cocok untuk proses satu-arah |

**Aturan penting:** fitur stateful (Interview, CS) **selalu pakai Python-Native**, tidak peduli `USE_N8N` di-set apa. Toggle `USE_N8N` cuma mempengaruhi fitur linear (job matching) — kalau `false`, fallback ke Python-Native juga (untuk jaga-jaga kalau server n8n down).

**Implikasi yang perlu diperhatikan:**
- **`llm_client.py` (sumber bug Groq, §2.5) ada di Pipeline 1**, independen dari n8n. Artinya perbaikan bug Groq **harus dilakukan di kode Python**, bukan dengan "reroute lewat n8n" — n8n tidak akan menyentuh jalur ini sama sekali.
- **Kemungkinan ada duplikasi fitur antar 2 pipeline** — CV Reviewer/Career Consultant kemungkinan ada di KEDUA tempat: sebagai file `agents/*.py` (Python-Native) DAN sebagai workflow n8n terpisah (§2.7). Perlu dikonfirmasi ke Antigravity: file `agents/*.py` yang mana sebenarnya dipanggil live oleh Streamlit sekarang, supaya tidak salah maintain versi yang "mati".
- **§7B (arsitektur target) perlu direvisi** — proposal "konsolidasikan semua ke n8n" bertentangan dengan alasan desain Dual-Pipeline (state & guardrail lebih stabil di Python untuk fitur stateful). Lihat catatan revisi di §7B.

### 2.7 Temuan Besar: Family Workflow Terpisah (1-6) — Bagian dari Pipeline 2

> **Update 21 Juli (dilaporkan Antigravity, belum diverifikasi independen):** 6 workflow ini dikonfirmasi **legacy** — sisa arsitektur sebelum konsolidasi ke V4. App live sekarang **hanya memanggil workflow V4** (1 webhook terpusat) lewat Dual-Pipeline (§2.6). Aman dihapus dari n8n untuk pembersihan. Ini menjawab §13 pertanyaan #7 dan #9 lebih pasti — tapi tetap disarankan verifikasi 1x lagi langsung ke kode sebelum benar-benar menghapus (menghapus workflow lebih sulit dibatalkan dibanding sekadar membaca kode).

Selain "JobMatch AI V4", ditemukan **6 workflow n8n individual terpisah** di Drive — masing-masing punya webhook sendiri, tidak saling terhubung dengan V4:

| # | Nama Workflow | Endpoint | Fungsi | AI Provider |
|---|---|---|---|---|
| 1 | CV Job Matcher | `/job-match` | Cocokkan CV ke lowongan (pakai Qdrant `indonesian_jobs_gemini`) | OpenAI `gpt-4o` (versi lama) / campuran Gemini embedding + OpenAI chat (versi lebih baru) |
| 2 | CV Reviewer | `/cv-review` | Skor ATS + feedback terstruktur (kelebihan, area perbaikan, keyword terdeteksi) | OpenAI `gpt-4o` |
| 3 | **ATS CV Generator** | `/ats-generate` | **Generate ulang CV jadi ATS-friendly** — ini fitur yang sempat saya bilang "belum ada", ternyata ADA di sini | OpenAI `gpt-4o` |
| 4 | Career Consultant | `/career-chat` | Konsultasi karir berbasis CV, ada versi yang juga pakai tool cari lowongan (Qdrant) sebagai referensi tren pasar | OpenAI `gpt-4o` |
| 5 | Mock Interview | `/mock-interview` | Simulasi interview bertahap (5-7 pertanyaan + ringkasan skor) | OpenAI `gpt-4o` |
| 6 | SQL Agent | `/sql-query` | Agent SQL generator + eksekutor berdiri sendiri, read-only, ke tabel `jobs` di Aiven | OpenAI `gpt-4o` |

**3 masalah yang ditemukan dari family workflow ini:**

1. **Provider AI tidak konsisten dengan keputusan Gemini-only.** Semua 6 workflow ini pakai kredensial `OpenAI account` (`gpt-4o`) — bertentangan dengan instruksi konsolidasi ke Gemini. Ini **selain** Groq yang sudah ditemukan di `llm_client.py` — berarti ada 2 provider "nyasar" yang perlu dibersihkan, bukan cuma 1.
2. **Terpisah dari V4, kemungkinan versi lebih lama.** File 1-6 terakhir diubah 2 & 15 Juli, sedangkan V4 diubah 21 Juli (hari ini). Kemungkinan besar family 1-6 ini adalah iterasi arsitektur sebelumnya (pendekatan "microservice per fitur") yang kemudian mulai dikonsolidasi jadi 1 workflow gabungan multi-agent (V3 → V4). **Perlu dipastikan ke kamu: apakah Streamlit app sekarang masih manggil endpoint-endpoint individual ini (`/cv-review`, `/ats-generate`, dst), atau sudah pindah semua ke webhook tunggal V4 (`/job-assistant`)?** Ini menentukan mana yang harus dianggap "arsitektur aktif" di PRD.
3. **File terduplikasi di 3 folder Drive berbeda** (kemungkinan cuma backup, tapi perlu dikonfirmasi) — supaya tidak ada kebingungan versi mana yang paling baru saat mau diedit.

**Detail penting fitur #3 (ATS CV Generator) untuk requirement "versi ID & EN":**
System prompt-nya berbunyi *"Tulis dalam bahasa yang sama dengan CV asli (Indonesia/Inggris)"* — artinya **1 kali panggilan API cuma hasilkan 1 bahasa**, ikut bahasa CV asli. Untuk requirement brief "generate versi ID **dan** EN sekaligus", workflow ini perlu salah satu dari: (a) dipanggil 2 kali dengan instruksi bahasa berbeda tiap kali, atau (b) system prompt-nya direvisi untuk selalu hasilkan 2 versi dalam 1 respons.

**Kemungkinan jawaban untuk pertanyaan terbuka soal "3 agent literal" (§13):** Workflow **#6 "SQL Agent"** ini justru sudah berupa agent SQL yang berdiri sendiri (punya webhook sendiri, generate + eksekusi query sendiri) — beda dari pola "tool di dalam AI Agent" yang dipakai V4. Kalau family 1-6 ini yang jadi arsitektur final (bukan V4), berarti struktur "3 agent terpisah" sesuai brief JCAI justru **sudah lebih dekat terpenuhi** lewat pendekatan modular ini, dibanding pola V4.

### 2.8 Audit Peran Agent CS/HRD: Veronika (CS) & Leonardo (HRD)

> **Update 21 Juli (dilaporkan Antigravity):** dikonfirmasi **non-blocking** — boleh ditunda ke fase pengembangan berikutnya, tidak menghalangi rilis/demo sekarang. Langkah teknisnya juga dikonfirmasi sederhana: buat collection `hrd_knowledge` baru di Qdrant, update node Leonardo supaya mengarah ke situ, tambahkan system prompt (sudah ada draft-nya di §7C.1).

Konfirmasi dari kamu: **Leonardo = agent HRD**, **Veronika = agent Chat CS**. Setelah dicek ulang ke file JSON, ini yang sesungguhnya terjadi di level implementasi:

**Semua resource terkait (audit lengkap):**

| Resource | Collection/Tabel | Terhubung ke | Status |
|---|---|---|---|
| Qdrant (utama, tanpa label khusus) | `indonesian_jobs_gemini` | AI Agent (Job Search) — jalur live, terhubung Webhook | ✅ dipakai, ini jalur utama yang sudah live |
| Aiven (utama, tanpa label khusus) | tabel `jobs` | AI Agent (Job Search) — jalur live | ✅ dipakai |
| Qdrant 1 (Jobs Vector DB) | `indonesian_jobs_gemini` (collection sama persis dengan yang utama) | "HR Knowledge Tool" → Main Orchestrator Agent | 🧟 draft yatim. **Nama tool "HR Knowledge Tool" tapi isinya data lowongan kerja, bukan data HRD** — kemungkinan salah tempel saat drafting, atau memang belum sempat diarahkan ke collection HRD yang benar |
| Aiven 1 (Primary SQL) | tabel `jobs` (duplikat) | Main Orchestrator Agent | 🧟 draft yatim, redundan dengan Aiven utama |
| Qdrant 2 (CS Memory DB) | `cs_memory` | "CS Knowledge Tool" → **dipakai Veronika DAN Leonardo, sama-sama** | ⚠️ belum dibedakan isi per agent |
| Aiven 2 (Telemetry/Kafka) | tabel log (skema belum pasti) | **Log dari Veronika DAN Leonardo, sama-sama** | ⚠️ untuk simpan riwayat percakapan, dipakai bersama |

**Gap yang ditemukan:** Veronika dan Leonardo secara struktur di JSON adalah **"kembar identik"** — sama-sama baca dari `cs_memory`, sama-sama tulis log ke Aiven 2, cuma dipicu field webhook berbeda (`cs_query_veronika` vs `cs_query_leonardo`). Supaya Leonardo benar-benar jadi spesialis HRD (bukan cuma nama), datanya perlu dipisah dari Veronika.

**Rekomendasi pemisahan tugas yang jelas:**

| Agent | Peran | Sumber data yang SEHARUSNYA |
|---|---|---|
| **Leonardo (HRD)** | Jawab pertanyaan seputar HRD — kebijakan SOP, appraisal, training, rubrik penilaian | Collection Qdrant `hrd_knowledge` (rencana di §5.5 — isi dari SOP_Form_SDM, Assessment_Center, Training_Modules, dst), **bukan** `cs_memory` |
| **Veronika (CS)** | Jawab pertanyaan umum pengguna app — cara pakai, troubleshoot, FAQ | Collection Qdrant `cs_memory` tetap relevan untuk ini — cocok untuk simpan riwayat & FAQ percakapan |
| Keduanya | Log percakapan untuk audit/analitik | Aiven 2 tetap dipakai bersama — ini memang wajar sebagai tabel log umum, tidak perlu dipisah per agent, cukup ada kolom `agent_name` untuk membedakan (sudah ada di `cs_agent_log` pada `create_tables_mysql.sql`) |

**Action item konkret:** ganti collection yang dipakai `CS Knowledge Tool` khusus untuk Leonardo supaya menunjuk ke `hrd_knowledge`, bukan `cs_memory` — ini butuh 2 node Vector Store Tool terpisah (1 untuk Leonardo ke `hrd_knowledge`, 1 untuk Veronika ke `cs_memory`), bukan 1 tool yang dipakai bersama seperti sekarang.

**Soal `Qdrant 1 (Jobs Vector DB)` / `HR Knowledge Tool`:** ini node yatim yang namanya membingungkan — disarankan **dihapus saja** dari file workflow (bukan diperbaiki), karena sudah redundan dengan Qdrant utama yang live, dan `hrd_knowledge` yang benar untuk Leonardo perlu dibuat sebagai collection baru, bukan reuse node lama ini.

---

## 3. Goals & Success Metrics

| Goal | Metric | Target |
|---|---|---|
| Bug production hilang | Fitur Analisis AI tidak error | 0 error `model_decommissioned` |
| CV kandidat lolos parsing ATS | Skor ATS Parsing (Scoring_Rubric kategori A) | ≥ 90/100 |
| CV kandidat kuat kualitatif HRD | Skor Konten/HRD (kategori B) | ≥ 80/100 |
| Kandidat dapat CV siap pakai | CV ATS-optimized EN + ID ter-generate | 100% CV yang diproses — **⚠️ workflow ada, belum terintegrasi/lengkap (§2.7, §11)** |
| Kandidat dapat rekomendasi lowongan | Jumlah lowongan match ditampilkan | 10 lowongan per CV |
| Efisiensi biaya API | Kuota embedding Gemini gratis terpakai untuk isi data awal | ≤ 596 request, 1 key, ~7 menit (§5.5) |
| Data lengkap & bisa dipercaya | % file HRD toolkit sudah masuk knowledge base | ~85% (§5.3) |
| **Lulus penilaian akademik** | Skor rubrik resmi JCAI | Sesuai target kelompok |

**Ringkasan Rubrik Penilaian Resmi JCAI** (skala 1-5 per kriteria):

| Bagian | Kriteria | Bobot |
|---|---|---|
| Kelompok — Kualitas Proyek (40%) | Fungsionalitas & Implementasi | 15% |
| | Kompleksitas Teknis & Inovasi | 15% |
| | Desain UX/UI | 10% |
| Kelompok — Kualitas Presentasi (40%) | Struktur & Alur Presentasi | 15% |
| | Demo Produk (Live Demo) | 15% |
| | Visual & Materi Pendukung | 10% |
| Kelompok — Tanya Jawab (20%) | Pemahaman Proyek | 15% |
| | Kerjasama Tim | 5% |
| Individu — Delivery (40%) | Kejelasan Bicara + Bahasa Tubuh + Keterlibatan Audiens | 40% |
| Individu — Konten Teknis (40%) | Penjelasan bagian sendiri + Jawaban T&J | 40% |
| Individu — Kontribusi (20%) | Kualitas commit + Manajemen tugas/waktu | 20% |

**Implikasi:** "Kompleksitas Teknis & Inovasi" (15%) kemungkinan besar dinilai dari arsitektur multi-agent + integrasi 3 layanan cloud (Aiven, Qdrant, N8N) — bukan cuma "boleh ada", tapi kemungkinan poin penilaian utama.

---

## 4. Target Users

**Persona 1 — Job Seeker (pengguna utama):** upload CV → dapat skor ATS, saran perbaikan, CV versi optimized (ID & EN), 10 lowongan cocok.

**Persona 2 — Pemilik produk (kamu):** butuh sistem murah dijalankan (tier gratis semaksimal mungkin), mudah di-maintain meski non-teknis, data bisa diperluas tanpa nulis ulang sistem.

---

## 5. Data Inventory & Arsitektur Data

### 5.1 Struktur Sumber Data (Google Drive, folder "data hrd")

```
data hrd/
├── 8. 10 TOOL HRD (ZIP 1 - HRD Toolkit, 170 file)
│   ├── Tools 1 - Kamus Kompetensi Hard/Soft Skills      -> sudah diekstrak
│   ├── Tools 2 - SOP + 20 Form Bidang SDM               -> sudah diekstrak
│   ├── Tools 3 - Instrumen Assessment Center (2 level)  -> sudah diekstrak
│   ├── Tools 4 - Employee Satisfaction Survey           -> sudah diekstrak
│   ├── Tools 5 - Training Plan & Modul Training          -> SEBAGIAN
│   ├── Tools 6 - Competency-based Interview Questions    -> sudah diekstrak
│   ├── Tools 7 - Salary Grade & Compensable Factors      -> sudah diekstrak
│   ├── Tools 8 - Katalog KPI (143 KPI, 16 fungsi)        -> sudah diekstrak
│   ├── Tools 9 - Program Strategis HR                    -> SEBAGIAN
│   └── Tools 10 - Form Performance Appraisal KPI         -> sudah diekstrak
├── BONUS CV ATS/ (6 contoh CV nyata)                     -> sudah diekstrak
├── dataset/ (folder terpisah, isi belum ditelusuri)
├── Tracker HR/ (folder terpisah, isi belum ditelusuri)
└── ATS_CV_Knowledge_Base_lengkap.xlsx (16 sheet, hasil ekstraksi)
```

### 5.2 Knowledge Base (`ATS_CV_Knowledge_Base_lengkap.xlsx`, 16 sheet)

| Sheet | Isi | Jumlah Baris |
|---|---|---|
| Panduan | Dokumentasi cara pakai tiap sheet | - |
| ATS_Scoring_Template | Template skor 1 CV vs 1 lowongan | 14 kriteria |
| Scoring_Rubric | Master bobot & indikator penilaian (total bobot 100%) | 14 kriteria |
| Keyword_Bank | Kompetensi hard/soft skill per 6 bidang | 6 bidang |
| CV_Examples | Analisis 6 CV nyata (skor rata-rata 63.8/100) | 6 CV |
| Common_Mistakes | 5 pola kesalahan CV yang sering ditemukan | 5 pola |
| KPI_Katalog | Katalog KPI per fungsi perusahaan | 143 KPI, 16 fungsi |
| Interview_Questions | Pertanyaan competency-based interview | 44 baris |
| Salary_Grade_Reference | Referensi grading & skala gaji | 68 baris |
| Inventaris_Sumber_File | Status ekstraksi seluruh 176 file sumber | 183 baris |
| SOP_Form_SDM | SOP + 20 form proses SDM lengkap | 21 item |
| Assessment_Center | 6 exercise x 2 level (Manajer/Supervisor) | 12 baris |
| Employee_Satisfaction_Survey | 25 item kuesioner + contoh hasil (77 responden) | 33 baris |
| Training_Modules | Matriks training 8 fungsi x 4 level + 10 modul siap pakai | 42 baris |
| HR_Strategic_Program | Roadmap program strategis HR 2011-2015 | 16 baris |
| Job_Database | 473 lowongan kerja riil | 473 baris |

### 5.3 Yang Belum Lengkap (transparansi status)

| Item | Status |
|---|---|
| Folder "Silabus Training" (9 fungsi x 4 level, ~34 sub-folder) | Struktur dipetakan, isi detail BELUM ditranskrip (estimasi 60-100+ file) |
| File "HR Programs and Action Plan.xls" | Belum tertranskrip (format lama) |
| Folder `dataset/` dan `Tracker HR/` di Drive | Belum ditelusuri isinya |

Ketiga item ini di luar jalur kritis untuk fitur inti — bisa dikerjakan belakangan.

### 5.4 Pembagian Data ke Aiven vs Qdrant

| Data | Tujuan | Alasan |
|---|---|---|
| Job_Database, Scoring_Rubric, Salary_Grade_Reference, KPI_Katalog | **Aiven (MySQL)** | Data terstruktur, perlu filter presisi (lokasi, gaji, kategori) |
| Job_Database (judul+deskripsi), SOP_Form_SDM, Assessment_Center, ESS, Training_Modules, HR_Strategic_Program, Keyword_Bank, Common_Mistakes | **Qdrant (vector)** | Perlu dicari "berdasarkan makna" (semantic search) |

### 5.5 Rencana Persiapan Data untuk Embedding (Gemini `gemini-embedding-001`, free tier)

> **Status:** collection `indonesian_jobs_gemini` (baris #1) **sudah nyata dipakai** workflow n8n. Collection `hrd_knowledge` (baris #2-8) **masih rencana, belum ada di workflow n8n** — perlu diputuskan apakah HRD Toolkit diikutsertakan atau project fokus ke Job Dataset saja (§13).

| # | Sumber | Satuan chunk | Jumlah chunk | Est. token/chunk | Est. total token | Collection tujuan |
|---|---|---|---|---|---|---|
| 1 | Job_Database | `job_title + job_description` per lowongan | 473 | ~300 | ~142.000 | `indonesian_jobs_gemini` |
| 2 | SOP_Form_SDM | 1 baris | 21 | ~150 | ~3.150 | `hrd_knowledge` |
| 3 | Assessment_Center | 1 baris | 12 | ~250 | ~3.000 | `hrd_knowledge` |
| 4 | Employee_Satisfaction_Survey | 1 item | 33 | ~40 | ~1.300 | `hrd_knowledge` |
| 5 | Training_Modules | 1 baris (skip "(pola sama)") | ~30 | ~150 | ~4.500 | `hrd_knowledge` |
| 6 | HR_Strategic_Program | 1 baris | 16 | ~100 | ~1.600 | `hrd_knowledge` |
| 7 | Keyword_Bank | 1 bidang | 6 | ~100 | ~600 | `hrd_knowledge` |
| 8 | Common_Mistakes | 1 pola | 5 | ~80 | ~400 | `hrd_knowledge` |
| | **TOTAL** | | **≈596 chunk** | | **≈157.000 token** | 2 collection |

**Kuota vs kebutuhan** (per key gratis: 90 req/menit, 27.000 token/menit, 950 req/hari):
- 596 request jauh di bawah limit 950/hari → **1 key cukup** untuk isi data awal, ~7 menit dengan jeda 0,7 detik/request.
- Token per menit (~25.500) mepet di limit 27.000 — mitigasi: potong tiap chunk maksimal ~2.000 karakter.

**Fungsi 10 key:**

| Skenario | Key yang dipakai |
|---|---|
| Isi data awal (one-time) | 1 key cukup |
| Traffic user harian (tiap CV upload = 1x embed) | Rotasi 10 key |
| Update Job_Database berkala | 1 key cukup (<900 lowongan baru/hari) |
| Key utama kena limit/error 429 | Key cadangan otomatis (failover) |

**Checklist sebelum embedding dijalankan:**
- [ ] Skip baris kosong/placeholder (`(pola sama)` di Training_Modules, dll)
- [ ] Potong `job_description` >2.000 karakter sebelum kirim ke API
- [ ] `output_dimensionality = 768` konsisten di semua chunk
- [ ] Simpan `id` unik per chunk (kolom `qdrant_point_id` di tabel `jobs`)
- [ ] Cache lokal (`embedding_cache.json`) aktif dari run pertama

---

## 6. Functional Requirements (MoSCoW)

*🎓 = wajib dari brief resmi JCAI · ⭐ = nilai tambah resmi (Advance Requirement) · ✅ = sudah live & terverifikasi · 💡 = ide tambahan di luar brief*

### Must Have
- 🎓✅ **Multi-agent system di N8N**, di-deploy sebagai REST API via webhook — implementasi nyata: 1 AI Agent + 2 tools (lihat §2.2 soal risiko akademik).
- 🎓✅ **Upload & parsing CV** (PDF/DOCX).
- 🎓✅ **Agent bisa jawab dari vectorDB** — job title/description dari Qdrant.
- 🎓✅ **Agent bisa jawab dari SQL database** — `salary_min`/`salary_max`/`work_type` dari Aiven.
- 🎓✅ **Streamlit terhubung ke webhook N8N**.
- ✅ **3 mode sumber lowongan** — Dari Dataset (AI Match), Cari di Internet, Scrape Lowongan Live (detail §2.4).
- 💡 **Skoring CV vs ATS** — Scoring_Rubric (ATS Parsing 30%, Konten/HRD 65%, Match Scoring 5%).
- 💡 **Analisis kelemahan CV + saran perbaikan** — dicocokkan ke Common_Mistakes. *(🚨 saat ini error, lihat §2.5)*
- 💡⚠️ **Generate CV ATS-optimized** — versi ID & EN. **Workflow-nya ada** (`3 - ATS CV Generator`) tapi belum terintegrasi ke Streamlit & belum penuhi requirement ID+EN otomatis (§2.7, §11).

### Should Have
- ⭐✅ **Job matching dari CV** — upload CV → rekomendasi lowongan cocok (sudah live).
- ⭐✅ **Career consultation** — berdasarkan CV (halaman "Konsultasi Karir" sudah ada).
- 💡✅ **Simulasi mock interview** — halaman "Mock Interview" sudah ada.
- 💡 **Rekomendasi training** — modul relevan dari Training_Modules kalau kandidat diterima.

### Could Have
- 💡 **Dashboard tracking** — riwayat CV & progres skor.
- 💡 **Auto-refresh Job_Database** — pipeline n8n terjadwal.

### Won't Have (fase awal)
- Integrasi langsung ke sistem ATS resmi perusahaan pihak ketiga.
- Auto-apply ke lowongan tanpa konfirmasi kandidat.

---

## 7. Arsitektur Teknis (kondisi nyata, bukan rencana)

```
   TAHAP 1 — ETL DATA AWAL (sekali/berkala)
   ┌───────────────────────────────────────┐
   │   n8n Workflow: "Ingest"                 │
   │   xlsx -> split per sheet                │
   └───────────────────────────────────────┘
          │                        │
   data terstruktur          data teks bebas (596 chunk, §5.5)
          │                        │
          ▼                        ▼
   ┌─────────────┐        ┌──────────────────────┐
   │ Aiven MySQL  │        │ Gemini Embedding API   │
   │ tabel jobs   │        │ gemini-embedding-001   │
   └─────────────┘        │ 1 key cukup (§5.5)     │
          │                └──────────────────────┘
          │                           │
          │                           ▼
          │                ┌──────────────────────┐
          │                │ Qdrant (vektor)        │
          │                │ indonesian_jobs_gemini     │
          │                │ (473 point, sudah ada)  │
          │                │ hrd_knowledge (rencana) │
          │                └──────────────────────┘
          │                           │
          └─────────────┬─────────────┘
                         │
   TAHAP 2 — SISTEM AGENT (live, webhook ON) — sesuai V4 (§2.5A)
                         ▼
   ┌───────────────────────────────────────────────────────────┐
   │   n8n Workflow: "JobMatch AI V4"                              │
   │                                                                │
   │   Streamlit → Webhook → Request Router (Switch, by mode)       │
   │                              │                                 │
   │        ┌─────────────────────┼─────────────────────┐           │
   │        ▼                     ▼                     ▼           │
   │  ┌───────────┐       ┌───────────┐         ┌───────────┐       │
   │  │Main Orch. │       │ Veronika  │         │ Leonardo  │       │
   │  │(Job Search)│       │   (CS)    │         │  (HRD)*   │       │
   │  └─────┬─────┘       └─────┬─────┘         └─────┬─────┘       │
   │        │                   │                     │             │
   │   Vector Store Tool    CS Knowledge Tool    CS Knowledge Tool   │
   │   + SQL Tool           (cs_memory)          (cs_memory)*        │
   │        │                   │                     │             │
   │        ▼                   ▼                     ▼             │
   │  indonesian_jobs_       Qdrant 2              Qdrant 2          │
   │  gemini + tabel jobs    (cs_memory)           (cs_memory)*      │
   │                                                                │
   │   Semua 3 agent berbagi 1 node: Gemini Chat Model               │
   │   (gemini-2.5-flash)                                            │
   └───────────────────────────────────────────────────────────┘
                         ▲
                         │  HTTP POST ke webhook (path: job-assistant)
   ┌───────────────────────────────────────┐
   │   Streamlit App — JobMatch AI            │
   │   jobsmatch.streamlit.app                 │
   │   - 5 step: Upload CV → Cari Loker →     │
   │     Review → Konsultasi Karir → Interview │
   │   + Sentry (error tracking)               │
   └───────────────────────────────────────┘
```
*Leonardo secara struktur masih identik dengan Veronika (§2.8) — belum benar-benar HRD sampai dipisah collection & system prompt-nya.

**Pembagian tugas (kondisi nyata V4):**

| Komponen | Tipe node n8n | Tugas | Sumber data |
|---|---|---|---|
| Request Router | `n8n-nodes-base.switch` | Baca `cs_query_veronika`/`cs_query_leonardo`/`query` dari body, arahkan ke agent yang sesuai | - |
| Main Orchestrator Agent | `@n8n/n8n-nodes-langchain.agent` (toolsAgent) | Jawab pertanyaan lowongan — pakai Vector Store Tool + SQL Tool | Qdrant `indonesian_jobs_gemini`, Aiven tabel `jobs` |
| Veronika (CS Agent) | `@n8n/n8n-nodes-langchain.agent` | Support umum, belum ada system prompt | Qdrant `cs_memory`, Aiven `cs_agent_log` (insert-only) |
| Leonardo (CS Agent, seharusnya HRD) | `@n8n/n8n-nodes-langchain.agent` | Seharusnya jawab pertanyaan HRD, tapi saat ini masih identik Veronika | Qdrant `cs_memory` (seharusnya `hrd_knowledge`) |

**Family workflow terpisah (§2.7), belum terhubung ke diagram di atas:** CV Job Matcher, CV Reviewer, ATS CV Generator, Career Consultant, Mock Interview, SQL Agent (endpoint masing-masing sendiri, pakai OpenAI, perlu diklarifikasi apakah masih dipanggil Streamlit atau sudah digantikan V4 — §13 pertanyaan #7).

**Stack:**
- **Frontend**: Python + Streamlit — UI saja, panggil REST API N8N
- **Backend/Agent logic**: N8N workflow, di-deploy sebagai REST API via webhook
- **Vector store**: Qdrant Cloud
- **Relational store**: Aiven for MySQL
- **AI model**: Gemini di V4 (embedding + generatif, 100% konsisten); **OpenAI di family workflow 1-6** (§2.7, kontradiksi keputusan Gemini-only); Groq di `llm_client.py` Streamlit (bug §2.5)
- **Monitoring**: Sentry

---

## 7A. Pipeline Teknis AI: Parsing → Chunking → Embedding → Vector Store

Bagian ini penting untuk sesi Tanya Jawab (rubrik "Kompleksitas Teknis & Inovasi" dan "Penjelasan Teknis" individu) — jadi saya pisahkan tegas mana yang **✅ sudah pasti terkonfirmasi** dari file yang saya baca langsung, vs **❓ belum terverifikasi** (masih perlu dicek ke kode/n8n UI sebelum dipresentasikan sebagai fakta).

### 1. Parsing

| Tahap | Sumber input | Metode | Status |
|---|---|---|---|
| CV kandidat | PDF/DOCX yang diupload user | `cv_processor.py` — "membaca & mengekstrak teks dari PDF/Word" | ❓ Library spesifik (PyPDF2/pdfplumber/python-docx/dll) belum saya lihat isi kodenya |
| Job_Database | `jobs__1__jsonl.xlsx` / JSONL | Data sudah terstruktur (kolom job_title, job_description, dll) — tidak perlu parsing dokumen, cuma baca tabel | ✅ |
| HRD Toolkit | .docx/.xlsx/.doc/.ppt (170 file Drive) | Dibaca via Google Drive API (`read_file_content`) yang otomatis convert ke representasi teks | ✅ (proses saya sendiri saat menyusun Knowledge Base) |

### 2. Chunking

**Prinsip: 1 chunk = 1 unit yang bisa berdiri sendiri secara makna**, bukan dipotong per-N-karakter secara buta. Strategi per sumber (detail tabel lengkap di §5.5):

| Sumber | Unit 1 chunk |
|---|---|
| Job_Database | `job_title + job_description` digabung jadi 1 chunk per lowongan (473 chunk) — tidak dipecah lagi karena masih di bawah limit 2.048 token per input `gemini-embedding-001` |
| CV kandidat | Kemungkinan 1 chunk = keseluruhan CV (untuk query embedding saat matching) — ❓ perlu dicek apakah `cv_processor.py`/`rag_agent.py` memecah CV per section (Experience/Education/Skills) atau kirim utuh |
| HRD Knowledge Base | 1 chunk = 1 baris per sheet (1 SOP, 1 exercise assessment, 1 item kuesioner, dst) — lihat tabel §5.5 |

**Tidak ada overlap/sliding window** di skema saat ini (beda dari pola chunking dokumen panjang seperti RAG PDF book) — karena sumber data sudah alami berbentuk unit-unit pendek (per baris/per lowongan), bukan dokumen panjang yang perlu dipotong paksa.

### 3. Embedding

| Parameter | Nilai | Status |
|---|---|---|
| Model | `gemini-embedding-001` | ✅ dari node `Gemini Embeddings` di workflow n8n |
| Dimensi output | 768 (di-truncate dari default 3072 via Matryoshka Representation Learning) | ⚠️ **ini rencana saya di §5.5, belum terkonfirmasi apakah node n8n `Gemini Embeddings` sudah di-set eksplisit ke 768** — parameter node itu di file JSON kosong (`{}`), artinya kemungkinan masih pakai default 3072. **Perlu dicek ke n8n UI.** |
| `task_type` | Idealnya `RETRIEVAL_DOCUMENT` saat indexing data, `RETRIEVAL_QUERY` saat user search — asimetri ini penting untuk kualitas hasil RAG | ❓ belum terverifikasi apakah node n8n `Gemini Embeddings` membedakan keduanya, atau pakai 1 task_type generik untuk semua |
| Rate limit free tier | 90 request/menit, 27.000 token/menit, 950 request/hari per key | ✅ (dari riset publik, §5.5) |

### 4. Vector Store

| Parameter | Nilai | Status |
|---|---|---|
| Provider | Qdrant Cloud | ✅ |
| Collection (Job Dataset) | `indonesian_jobs_gemini` | ✅ dari node `Qdrant Vector Store` di workflow n8n |
| Collection (HRD Knowledge, kalau jadi dipakai) | `hrd_knowledge` (rencana, belum dibuat) | ⬜ |
| Distance metric | ❓ **belum terverifikasi** — n8n default untuk `vectorStoreQdrant` biasanya Cosine, tapi tidak eksplisit ditulis di parameter node | ❓ |
| `contentPayloadKey` | `"document"` — field di payload yang dianggap sebagai teks utama untuk ditampilkan balik | ✅ dari file JSON |

### 5. Nama Model (Generatif)

| Peran | Node n8n | Model spesifik | Status |
|---|---|---|---|
| Chat/reasoning untuk semua agent (Main Orchestrator, Veronika, Leonardo) | `Gemini Chat Model` (`lmChatGoogleGemini`) | **`gemini-2.5-flash`** | ✅ terkonfirmasi eksplisit di file JSON V4 (`"modelName": "gemini-2.5-flash"`) — sudah tidak perlu ditebak lagi |
| Sisi Streamlit (yang error) | `llm_client.py` | `llama3-70b-8192` (Groq, **sudah decommissioned**, ini bug §2.5) — perlu diganti eksplisit ke `gemini-2.5-flash` supaya konsisten dengan yang dipakai n8n | 🚨 |

### Rekomendasi sebelum presentasi

Model chat (`gemini-2.5-flash`) dan nama collection sudah confirmed dari file V4 — tidak perlu ditebak lagi untuk itu. Yang **masih perlu dicek manual di n8n UI** sebelum presentasi: dimensi embedding aktual (apakah 768 atau default 3072) dan distance metric Qdrant (biasanya Cosine, tapi tidak eksplisit tertulis di file). Ini menyasar kriteria rubrik "Pemahaman Proyek" (15%) dan "Penjelasan Teknis" individu (25%) — dua kriteria berbobot besar yang butuh jawaban presisi, bukan perkiraan.

### 6. Berapa "Model Gemini" yang Dibutuhkan per Agent?

**Koreksi konsep dulu:** Gemini bukan software yang "diinstall dekat database" — itu API yang dipanggil lewat internet dari mana saja (n8n, Streamlit, di server manapun). Jadi pertanyaannya bukan "berapa Gemini yang perlu dipasang di dekat Aiven/Qdrant", tapi **"berapa node/binding Gemini yang perlu dikonfigurasi di n8n, dan pengaturan apa yang beda-beda per agent"**.

**Aturan teknis yang WAJIB diikuti (bukan pilihan):**
- Semua vektor dalam **1 collection Qdrant harus pakai model embedding & dimensi yang sama persis** — tidak boleh campur. Kalau `indonesian_jobs_gemini` di-embed pakai `gemini-embedding-001` dimensi 768, semua query pencarian ke collection itu juga wajib pakai kombinasi yang sama.

**Rekomendasi jumlah binding (bukan aturan wajib, tapi praktik yang masuk akal):**

| Binding | Jumlah disarankan | Alasan |
|---|---|---|
| **Embedding** (`Gemini Embeddings`) | **2 node** — 1 untuk collection `indonesian_jobs_gemini` (Job Search), 1 untuk `hrd_knowledge`+`cs_memory` (kalau dua collection ini dipakai model/dimensi yang sama, boleh 1 node dipakai bersama) | Yang menentukan jumlah node bukan jumlah agent, tapi **jumlah collection dengan konfigurasi embedding berbeda** |
| **Chat/LLM** (`Gemini Chat Model`) | **1 node sudah cukup** — dan ini persis kondisi nyata di V4 sekarang: 1 node `Gemini Chat Model` (`gemini-2.5-flash`) dipakai bersama oleh Main Orchestrator, Veronika, dan Leonardo. Kalau Leonardo (HRD) butuh gaya jawab lebih formal/presisi dibanding Veronika (CS) yang lebih santai, **cukup beda `systemMessage` di masing-masing node Agent**, tidak perlu bikin node Gemini Chat Model baru | Pemisahan "kepribadian" agent dilakukan lewat parameter `systemMessage` di node Agent-nya masing-masing, bukan lewat model Gemini yang dipakai — modelnya boleh tetap sama persis |
| **Kredensial API key** | Bebas pakai 1 key untuk semua node di atas untuk development; baru rotasi ke 10 key kalau traffic produksi tinggi (§5.5) | Rate limit Gemini berlaku per project/key, bukan per node — banyak node tidak otomatis berarti banyak kuota |

**Kesimpulan singkat:** Leonardo dan Veronika **tidak butuh Gemini terpisah untuk alasan teknis/performa** — yang mereka butuh adalah **collection Qdrant terpisah** (§2.8) supaya jawabannya relevan sesuai peran masing-masing. Pemisahan node Gemini Chat Model itu opsional, cuma relevan kalau kamu mau kepribadian/gaya bicara mereka beda secara sengaja.

---

## 7B. Arsitektur Target (Rencana Pengembangan — Menyatukan Family Workflow ke Pola Generik)

> ⚠️ **Revisi penting (setelah temuan Dual-Pipeline, §2.6):** Draft awal bagian ini menyarankan "pindahkan semua fitur ke n8n". Itu **keliru** — Dual-Pipeline sengaja memisahkan fitur stateful (Interview, CS) ke Python-Native karena alasan teknis nyata (state tracking & guardrail lebih stabil di kode langsung). Rekomendasi di bawah ini saya batasi ulang: **cuma berlaku untuk Pipeline 2 (N8N)** — konsolidasikan 6 workflow n8n yang berantakan jadi pola generik yang konsisten. **Jangan pindahkan Mock Interview atau CS chat ke n8n** — itu bertentangan dengan alasan Dual-Pipeline dibuat.

Target ini menggantikan kondisi n8n sekarang (V4 + 6 workflow terpisah yang tidak sinkron, §2.5–§2.7) khusus untuk fitur-fitur yang memang cocok di Pipeline 2 (linear/stateless): Job Search, CV Reviewer, CV Generator, Career Consultant. Tujuannya: **1 sistem n8n yang konsisten**, bukan 6+1 workflow dengan provider AI berbeda-beda.

### 7B.1 Prinsip Desain

1. **1 provider AI: Gemini saja** — untuk N8N (Pipeline 2) hapus OpenAI dari 6 workflow terpisah. Untuk Python-Native (Pipeline 1), hapus Groq dari `llm_client.py`. Kedua pipeline tetap terpisah secara arsitektur, tapi konsisten pakai 1 provider AI.
2. **Agent RAG dan Agent SQL jadi 2 workflow generik**, dipanggil semua orchestrator n8n lewat Execute Workflow — bukan tiap fitur bikin tool RAG/SQL sendiri-sendiri (ini penyebab duplikasi & inkonsistensi yang ditemukan di §2.7).
3. **Otomatis memenuhi syarat "3 agent literal" brief JCAI** (§13 pertanyaan #2) — Agent Utama, Agent RAG, Agent SQL jadi 3 komponen sungguhan yang terpisah, bukan disembunyikan sebagai tool di dalam 1 agent seperti pola V4 sekarang.

### 7B.2 Diagram Arsitektur Target

```
                    ┌─────────────────────────────────┐
                    │  Streamlit App (Webhook Entry)      │
                    │  Header Auth + field "mode" eksplisit│
                    └─────────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │       Request Router (Switch)       │
                    │  mode: job_search / hrd / cs /      │
                    │  cv_review / cv_generate /          │
                    │  career / interview                 │
                    └─────────────────────────────────┘
                                    │
        ┌──────────┬──────────┬────┴────┬──────────┬──────────┬──────────┐
        ▼          ▼          ▼         ▼          ▼          ▼          ▼
   ┌─────────┐┌─────────┐┌─────────┐┌────────┐┌─────────┐┌─────────┐┌─────────┐
   │Job Search││Leonardo ││Veronika ││   CV   ││   CV    ││ Career  ││  Mock   │
   │Orchestr. ││ (HRD)   ││  (CS)   ││Reviewer││Generator││Consult. ││Interview│
   └────┬────┘└────┬────┘└────┬────┘└───┬────┘└────┬────┘└────┬────┘└─────────┘
        │          │          │         │          │          │      (stateful,
        │          │          │         └────┬─────┘          │      Memory saja,
        └────┬─────┴──────────┘              │                │      tak perlu RAG/SQL)
             │                                │                │
             ▼                                ▼                ▼
      ┌─────────────┐                  ┌─────────────┐  ┌─────────────┐
      │  Agent RAG   │◄─────────────────│(parameter:   │  │ Agent RAG    │
      │  (generik,   │                  │ collection)  │  │ (jobs, utk   │
      │  1 workflow, │                                    │  tren pasar) │
      │  dipakai     │                                    └─────────────┘
      │  semua)      │
      └──────┬──────┘
             │  parameter "collection":
             │  - indonesian_jobs_gemini (Job Search, Career Consultant)
             │  - hrd_knowledge (Leonardo, CV Reviewer, CV Generator)
             │  - cs_memory (Veronika)
             ▼
      ┌─────────────┐        ┌─────────────┐
      │Gemini Embed. │        │  Agent SQL   │◄── dipakai Job Search,
      │(1 node saja) │        │  (generik,   │    Leonardo, CV Reviewer
      └─────────────┘        │  upgrade dari│
                              │  workflow #6)│
                              └──────┬──────┘
                                     │ parameter "table":
                                     │ - jobs (read-only)
                                     │ - scoring_rubric (read-only)
                                     │ - cs_agent_log (insert-only)
                                     ▼
                              ┌─────────────┐
                              │ Aiven MySQL  │
                              └─────────────┘

   Semua 7 orchestrator berbagi 1 node: Gemini Chat Model (gemini-2.5-flash)
```

> ⚠️ **Koreksi atas diagram di atas:** diagram ini digambar SEBELUM temuan Dual-Pipeline (§2.6). **Veronika (CS)** dan **Mock Interview** kemungkinan **seharusnya TIDAK dipindah ke n8n** — keduanya fitur stateful yang sengaja dipertahankan di Pipeline 1 (Python-Native) karena alasan state tracking & guardrail. Anggap diagram ini berlaku penuh untuk: Job Search, CV Reviewer, CV Generator, Career Consultant. Untuk Leonardo dan Veronika, statusnya **belum pasti** — perlu jawaban §13 pertanyaan #9 dulu sebelum diputuskan mereka masuk pipeline mana.

### 7B.3 Tabel Komponen & Tanggung Jawab

| Layer | Komponen | Peran | Sumber data | Pipeline |
|---|---|---|---|---|
| Entry | Request Router | Baca field `mode` eksplisit dari Streamlit, arahkan ke orchestrator yang tepat | - | N8N |
| **Agent RAG** (generik) | 1 workflow, dipanggil via Execute Workflow, parameter `collection` | Search semantik ke Qdrant, collection ditentukan pemanggil | Qdrant (3 collection) | N8N |
| **Agent SQL** (generik) | 1 workflow (upgrade dari workflow #6 "SQL Agent" yang sudah ada), parameter `table` | Generate + eksekusi query terstruktur, read-only kecuali tabel log | Aiven MySQL | N8N |
| Orchestrator: Job Search | Agent Utama (job) | Jawab pertanyaan lowongan — panggil Agent RAG(jobs) + Agent SQL(jobs) | - | N8N |
| Orchestrator: Leonardo | Agent Utama (HRD) | Jawab pertanyaan HRD — panggil Agent RAG(hrd_knowledge) + Agent SQL(scoring_rubric) — system prompt formal | - | N8N *(perlu konfirmasi, §13 #9)* |
| Orchestrator: Veronika | Agent Utama (CS) | Support umum app — kemungkinan lebih tepat tetap Python-Native (stateful) | - | ⚠️ Python-Native? (§2.6) |
| Orchestrator: CV Reviewer | Worker | Skor CV vs Scoring_Rubric — panggil Agent SQL(scoring_rubric) + Agent RAG(hrd_knowledge, untuk Common_Mistakes) | - | N8N |
| Orchestrator: CV Generator | Worker | Generate CV ID+EN sekaligus dalam 1 respons (prompt direvisi dari workflow #3 yang ada) — panggil hasil CV Reviewer + Agent RAG(hrd_knowledge, untuk Keyword_Bank & CV_Examples) | - | N8N |
| Orchestrator: Career Consultant | Worker | Konsultasi karir — panggil Agent RAG(jobs) untuk konteks tren pasar | - | N8N |
| Orchestrator: Mock Interview | Worker | Simulasi interview bertahap — stateful, tetap di Python-Native | - | Python-Native (§2.6) |

### 7B.4 Bagaimana Ini Menjawab Semua Temuan Audit

| Temuan audit | Diselesaikan bagaimana |
|---|---|
| OpenAI di 6 workflow terpisah (§2.7) | Semua orchestrator pakai 1 Gemini Chat Model bersama |
| Groq di `llm_client.py` Streamlit (§2.5) | Streamlit tidak lagi manggil LLM langsung — semua lewat n8n |
| "1 agent + 2 tools" vs "3 agent literal" (§13 #2) | Agent RAG dan Agent SQL jadi workflow terpisah beneran — brief terpenuhi literal |
| Leonardo/Veronika kembar identik (§2.8) | Beda parameter `collection` + beda system prompt per orchestrator |
| `HR Knowledge Tool` nama menyesatkan (§2.5A) | Diganti Agent RAG generik dengan parameter jelas, tidak ada nama tool yang salah lagi |
| CV Generator cuma 1 bahasa/panggilan (§2.7) | Prompt direvisi untuk selalu keluarkan 2 versi dalam 1 respons |
| 6 workflow redundan (RAG/SQL diduplikasi tiap fitur) | RAG dan SQL logic tidak diduplikasi, cukup 2 workflow generik dipanggil semua orchestrator |
| Duplikasi file di 3 folder Drive (§2.7) | Di luar scope arsitektur — perlu dibersihkan manual di Drive |

### 7B.5 Rencana Migrasi Bertahap

Ini bukan "bongkar semua sekaligus" — urutan migrasi yang disarankan, terintegrasi ke Fase 0-2 di §10:

1. Selesaikan Fase 0 dulu (bug Groq, bersihkan node yatim V4) — tidak tergantung keputusan arsitektur target.
2. **Putuskan dulu** jawaban §13 pertanyaan #7 (arsitektur mana yang aktif) sebelum mulai migrasi — percuma migrasi kalau ternyata Streamlit masih pakai endpoint lama.
3. Bangun Agent RAG generik dan Agent SQL generik (upgrade dari workflow #6) sebagai 2 workflow baru.
4. Migrasi 1 orchestrator dulu sebagai percontohan (disarankan: Leonardo, karena sekaligus menyelesaikan §2.8) — validasi pola generik-nya jalan baik.
5. Migrasi orchestrator lain satu per satu (Job Search, Veronika, lalu 4 worker dari family workflow).
6. Matikan/hapus 6 endpoint lama setelah semua orchestrator baru terverifikasi jalan dan Streamlit sudah dialihkan.

---

## 7C. Spesifikasi Prompt Engineering per Agent (Do & Don't)

Ditambahkan karena 2 alasan: (1) audit §2.5A menemukan Leonardo & Veronika **sama sekali tidak punya system prompt**, (2) kualitas prompt engineering kemungkinan masuk penilaian rubrik "Kompleksitas Teknis & Inovasi" (§3). Tabel di bawah berlaku untuk arsitektur target §7B maupun kalau mau langsung ditambal ke V4 sekarang.

### 7C.1 Leonardo (HRD Agent) — prioritas tertinggi, saat ini kosong total

| | Isi |
|---|---|
| **Do** | Jawab HANYA berdasarkan data dari `hrd_knowledge` (SOP_Form_SDM, Scoring_Rubric, Training_Modules, Common_Mistakes, dst) via Agent RAG. Sebutkan sumber dokumen kalau relevan (mis. "menurut SOP-02 Proses Rekrutmen..."). Kalau pertanyaan di luar cakupan knowledge base, jawab jujur tidak tahu, jangan mengarang. |
| **Don't** | Jangan memberi nasihat hukum ketenagakerjaan (UU Ketenagakerjaan, PHK, dll) seolah-olah otoritatif — arahkan ke HRD manusia/konsultan hukum untuk itu. Jangan membuat keputusan HR sungguhan (menerima/menolak kandidat, menentukan gaji final). Jangan membocorkan data kandidat lain. Jangan menjanjikan promosi/kenaikan gaji spesifik ke user. |

### 7C.2 Veronika (CS Agent) — saat ini kosong total

| | Isi |
|---|---|
| **Do** | Bantu soal cara pakai app (upload CV, baca skor, navigasi step), troubleshoot masalah teknis dasar, FAQ umum. Ramah dan santai. |
| **Don't** | Jangan menjawab pertanyaan substansi HRD (itu tugas Leonardo) — kalau ada, arahkan ke Leonardo. Jangan menjanjikan fitur yang belum ada di app. Jangan berpura-pura jadi manusia asli. |

### 7C.3 Main Orchestrator / Job Search Agent — sudah punya prompt dasar, perlu diperkuat

Prompt sekarang: *"Kamu adalah asisten pencari kerja. Gunakan tool yang tersedia... Jangan mengarang informasi lowongan yang tidak ada di database."* — sudah bagus, tambahan yang disarankan:

| | Isi |
|---|---|
| **Do** | Selalu sebut skor match sebagai estimasi ("berdasarkan kecocokan kata kunci", bukan jaminan diterima). Tampilkan sumber data tiap lowongan (dari dataset internal / hasil scrape live). |
| **Don't** | *(sudah ada)* Jangan mengarang lowongan/perusahaan yang tidak ada di database. Tambahan: jangan menjamin kandidat akan diterima atau dipanggil interview. |

### 7C.4 CV Reviewer & CV Generator (workflow #2 & #3, §2.7) — belum ada guardrail eksplisit

| | Isi |
|---|---|
| **Do** | Skor berdasarkan Scoring_Rubric yang konsisten (§5.4). Beri saran yang actionable dan spesifik ("tambahkan angka di bullet ini", bukan "perbaiki CV-mu"). Generate ulang CV **hanya menata ulang & memperkuat bahasa** dari pengalaman yang sudah ada di CV asli. |
| **Don't** | **Jangan pernah menambahkan pengalaman kerja, gelar, sertifikasi, atau pencapaian yang tidak disebutkan di CV asli user** — ini prinsip paling penting, karena CV Generator yang "mengarang" prestasi membantu user melakukan kebohongan di lamaran kerja. Jangan menjanjikan skor ATS resmi (selalu sebut ini estimasi internal, sudah ada disclaimer serupa di §12). |

### 7C.5 Mock Interview Agent (workflow #5) — sudah cukup baik, 1 tambahan penting

Prompt sekarang sudah bagus (1 pertanyaan per waktu, campur behavioral/technical/situational, professional tapi ramah). Tambahan wajib:

| | Isi |
|---|---|
| **Do** | Fokus pertanyaan ke kompetensi & pengalaman kerja relevan posisi. |
| **Don't** | **Jangan tanya hal yang termasuk kategori diskriminatif** — status pernikahan, rencana punya anak, usia, agama, suku, kondisi kesehatan/disabilitas — kecuali itu memang bona fide requirement pekerjaan (jarang). Ini bukan cuma etika, tapi juga demi kualitas simulasi: interview asli yang baik memang tidak menanyakan hal-hal itu. |

### 7C.6 Career Consultant (workflow #4)

| | Isi |
|---|---|
| **Do** | Berdasarkan CV yang sudah ada, beri insight tren pasar (pakai Agent RAG ke jobs). Bersikap suportif, tidak menghakimi pilihan karir. |
| **Don't** | Jangan menjanjikan hasil karir spesifik ("kamu pasti akan jadi manajer dalam 2 tahun"). Jangan meremehkan pilihan karir user. |

---

## 8. Alur Kerja Utama (User Flow)

```
1. Kandidat upload CV
        ▼
2. App parsing teks CV
        ▼
3. Skoring CV vs Scoring_Rubric
        ▼
4. Analisis kelemahan (Common_Mistakes + hasil skor)
        ▼
5. Generate CV versi ATS-optimized (ID & EN)
        ▼
6. Cari 10 lowongan match (3 mode: Dataset/Internet/Scrape Live)
        ▼
7. Tampilkan hasil: skor, saran, CV baru, 10 lowongan
        ▼
8. (Opsional) Konsultasi karir + Mock interview
        ▼
9. (Jika diterima) rekomendasi training dari Training_Modules
```

---

## 9. Non-Functional Requirements

| Kategori | Requirement |
|---|---|
| Biaya | Maksimalkan tier gratis Gemini embedding (90 req/menit, 950/hari per key); cache lokal agar tidak re-embed data yang sama |
| Keamanan | Semua kredensial (Aiven, Qdrant, Gemini) hanya di `.env`/n8n Environment Variables — tidak pernah hardcoded |
| Reliability | Pipeline n8n bisa dijalankan ulang tanpa duplikasi data (idempotent) |
| Auditability | Setiap update Knowledge Base dicatat di sheet Inventaris_Sumber_File |
| Bahasa | Semua output mendukung Bahasa Indonesia & Inggris |

---

## 10. Rencana Implementasi

**Fase 0 — Perbaiki Bug & Bersihkan Workflow (prioritas sekarang, urutan direvisi 21 Juli)**
- 🚨 **P0, LANGKAH PALING MENDESAK**: Klarifikasi ke Antigravity soal klaim "OpenAI fallback" di `llm_client.py` — kalau tidak disengaja, hapus dulu sebelum `git commit`+`push`, supaya konsisten Gemini-only (§2.5)
- Setelah klarifikasi di atas beres: **`git commit` + `git push`** — kode fix Groq sudah ada di lokal, tinggal deploy (§2.5)
- ⬜ *(sudah tidak mendesak, boleh ditunda)* ~~Sederhanakan `llm_client.py`~~ — sudah dikerjakan Antigravity, tinggal verifikasi poin di atas
- **Buat kredensial Header Auth** di n8n Settings > Credentials untuk node "Streamlit App (Webhook Entry)" — sudah direncanakan di V4 tapi belum dibuat manual, webhook belum aman tanpa ini
- ⬜ *(dikonfirmasi non-blocking, §2.8)* Pisahkan data Leonardo (HRD) dan Veronika (CS) — boleh dikerjakan di fase pengembangan berikutnya, bukan sekarang
- ⬜ *(dikonfirmasi legacy, §2.7)* Bersihkan 6 workflow family terpisah — aman dihapus setelah 1x verifikasi lagi, tidak mendesak
- Jalankan `create_tables_mysql.sql` (kolom `salary_min`/`salary_max`, tabel `cs_agent_log`) di Aiven MySQL Console kalau belum
- Putuskan: pola "1 AI Agent + 2 tools" untuk Job Search dipertahankan, atau dipecah jadi 3 agent literal sesuai brief (§13)
- ✅ ~~Node yatim, webhook duplikat, konsolidasi Gemini Chat Model, pemisahan izin Aiven 1 (read) vs Aiven 2 (insert)~~ — sudah diperbaiki di V4 (§2.5A), tidak perlu dikerjakan lagi

**Fase 1 — Data Foundation**
- ✅ Ekstrak HRD Toolkit ke Knowledge Base xlsx (16 sheet)
- ✅ Skema tabel Aiven MySQL (`create_tables_mysql.sql`)
- ✅ Script/template ingestion ke Aiven + Qdrant (Python & n8n)
- ⬜ Verifikasi jumlah data di production (473 lowongan + knowledge base HRD, kalau jadi dipakai)

**Fase 2 — Core Scoring & Generation (kerangka sudah ada, perlu direview)**
- ✅ `cv_analyzer_agent.py` + halaman Upload CV/ATS Score — cek apakah sudah pakai Scoring_Rubric dari knowledge base
- ⬜ Cek apakah sudah mengacu ke Common_Mistakes
- ⚠️ **Fitur generate CV ATS-optimized ADA sebagai workflow terpisah** (`3 - ATS CV Generator`, `/ats-generate`, §2.7) tapi belum terintegrasi ke alur 5-step Streamlit (tidak kelihatan di app) dan belum penuhi requirement ID+EN otomatis + RAG ke knowledge base — lihat spek upgrade lengkap di §11

**Fase 3 — Job Matching (sudah live)**
- ✅ 3 mode pencarian lowongan berjalan (§2.4)
- ⬜ Verifikasi kualitas match score & relevansi hasil

**Fase 4 — Fitur Lanjutan (sudah live)**
- ✅ Mock Interview, Konsultasi Karir sudah ada
- ⬜ (Opsional) lengkapi Silabus Training di knowledge base

**Fase 5 — Uji & Rilis**
- Testing end-to-end dengan 6 CV di sheet CV_Examples sebagai baseline
- Monitoring lewat Sentry pasca-perbaikan bug

---

## 11. Spesifikasi Fitur: Generate CV ATS-Optimized (Sudah Ada Workflow-nya, Perlu Konsolidasi)

**Update dari §2.7:** fitur ini **sudah ada** sebagai workflow terpisah (`3 - ATS CV Generator`, endpoint `/ats-generate`) — bukan lagi "belum dibangun sama sekali" seperti draft PRD sebelumnya. Bagian ini tetap saya pertahankan sebagai **spesifikasi target yang lebih lengkap**, karena workflow yang ada saat ini (pakai OpenAI, 1 bahasa per panggilan, prompt sederhana tanpa RAG ke knowledge base) belum memenuhi semua yang diminta brief (versi ID+EN otomatis, skor tertarget, berbasis Scoring_Rubric/Common_Mistakes/Keyword_Bank). Anggap ini **peta upgrade**, bukan spek dari nol.

### 11.1 Input & Output

| | Detail |
|---|---|
| Input | CV asli (hasil parsing dari step Upload CV) + (opsional) 1 lowongan target dari hasil "Cari Loker" |
| Output | 2 versi CV baru: **Bahasa Indonesia** dan **Bahasa Inggris**, keduanya ATS-optimized, ditarget skor mendekati 100 di Scoring_Rubric |

### 11.2 Sumber Data & Peran Masing-masing (simetris antar database)

| Sumber | Lokasi | Peran dalam generate CV |
|---|---|---|
| Scoring_Rubric | Aiven MySQL (tabel `scoring_rubric`) | Acuan skor target — tiap kriteria (ATS Parsing, Konten/HRD, Match Scoring) jadi checklist yang harus dipenuhi CV baru |
| Common_Mistakes | Qdrant `hrd_knowledge` (rencana, §5.5) | RAG — cari pola kesalahan yang mirip dengan isi CV asli, supaya tahu apa yang harus DIHINDARI |
| Keyword_Bank | Qdrant `hrd_knowledge` (rencana) | RAG — cari keyword hard/soft skill sesuai bidang kandidat & lowongan target, untuk memperkaya bahasa CV baru |
| CV_Examples | Qdrant `hrd_knowledge` (rencana) | RAG — referensi pola CV yang sudah pernah dianalisis dengan skor tinggi, sebagai "contoh gaya" |
| Job_Database (kalau ada lowongan target) | Qdrant `indonesian_jobs_gemini` | RAG — ambil requirement/keyword spesifik dari deskripsi lowongan target, supaya CV baru relevan ke lowongan itu |
| Salary_Grade_Reference | Aiven MySQL | Opsional — kalau CV baru perlu highlight level/grade yang sesuai |

**Kenapa harus simetris:** kalau cuma Aiven yang dipakai (skor rubrik doang), hasilnya CV yang "lolos angka" tapi bahasanya generik. Kalau cuma Qdrant yang dipakai (keyword & pola doang), hasilnya CV yang "kedengaran bagus" tapi belum tentu match skor rubrik secara terukur. **Keduanya perlu jalan bersama** — ini alasan teknis kenapa desainnya harus begini, bukan sekadar prinsip.

### 11.3 Alur Proses (5 langkah)

```
1. Ambil CV asli (teks hasil parsing)
        ▼
2. Skoring CV vs Scoring_Rubric (Aiven) → dapat skor per kriteria + kriteria mana yang masih rendah
        ▼
3. RAG ke hrd_knowledge (Qdrant): cari Common_Mistakes yang cocok dengan kelemahan CV,
   cari Keyword_Bank sesuai bidang, cari CV_Examples berskor tinggi sebagai referensi gaya
        ▼
4. (Kalau ada lowongan target) RAG ke indonesian_jobs_gemini: ambil keyword spesifik dari job_description
        ▼
5. Gemini (gemini-2.5-flash) susun ulang CV — 2 versi (ID & EN) — dengan instruksi eksplisit:
   perbaiki tiap kriteria yang skornya rendah, sisipkan keyword yang relevan, hindari pola dari
   Common_Mistakes, ikuti gaya dari CV_Examples berskor tinggi
        ▼
6. Skoring ulang hasil CV baru vs Scoring_Rubric (Aiven) — tampilkan skor sebelum vs sesudah
```

### 11.4 Rekomendasi Implementasi Teknis

- **Sebagai agent baru di n8n**, bukan ditambahkan ke agent yang sudah ada — supaya scope-nya jelas dan gampang di-debug terpisah dari Job Search/Veronika/Leonardo. Bisa disebut misalnya "Alex (CV Writer Agent)" mengikuti pola penamaan agent yang sudah ada.
- **Tools yang dibutuhkan agent ini** (mengikuti pola tool yang sudah ada di V4): 1 tool SQL read-only ke `scoring_rubric` (mirip `Aiven 1`), 1 tool RAG ke `hrd_knowledge` (collection baru, §5.5), 1 tool RAG ke `indonesian_jobs_gemini` kalau ada lowongan target.
- **Output disclaimer wajib**: sama seperti CV_Examples di knowledge base, skor yang ditampilkan adalah estimasi berdasar Scoring_Rubric internal, bukan skor sistem ATS resmi manapun (§10 Fase 5, konsisten dengan disclaimer yang sudah ada).

---

## 12. Risiko & Mitigasi

| Risiko | Mitigasi |
|---|---|
| Struktur "1 agent + 2 tools" tidak dianggap memenuhi "3 komponen agent" di brief | Konfirmasi ke mentor sebelum submit; siapkan opsi pemecahan jadi 3 agent kalau perlu |
| Kuota gratis Gemini habis saat traffic ramai | Rotasi 10 key, cache embedding, monitor lewat Sentry |
| Node workflow n8n yang rusak/yatim tidak sengaja aktif saat demo | Bersihkan di Fase 0 sebelum presentasi |
| Kredensial bocor lewat file/script yang dibagikan | Semua script pakai `.env`/Environment Variables |
| Skor ATS/HRD dianggap "resmi" oleh kandidat | Disclaimer di UI: skor adalah estimasi, bukan skor sistem ATS resmi manapun |
| MySQL response time (2419ms) jadi bottleneck saat traffic naik | Cek index tabel `jobs`, evaluasi region Aiven vs n8n |

---

## 13. Pertanyaan Terbuka untuk Kamu Putuskan

1. **Status deadline** — brief resmi 27 Nov 2025–6 Jan 2026 sudah lewat. Masih aktif dikerjakan, sudah submit, atau deadline diperpanjang?
2. **Struktur agent** — pola "1 agent + 2 tools" dipertahankan, atau dipecah jadi 3 agent literal sesuai kata-kata brief?
3. **HRD Knowledge Base** (`hrd_knowledge` collection) — jadi diikutsertakan ke agent, atau project fokus ke Job Dataset yang sudah jalan?
4. Folder `dataset/` dan `Tracker HR/` di Drive — ditelusuri sekarang atau nanti?
5. Silabus Training (~34 sub-folder) — dikerjakan sekarang atau ditunda?
6. **Peran Leonardo (HRD) & Veronika (CS)** — sudah jelas konsepnya (§2.8), tapi butuh keputusan: bikin collection `hrd_knowledge` baru sekarang untuk Leonardo, atau sementara biarkan berbagi `cs_memory` dulu sampai fitur lain selesai?
7. ~~Arsitektur mana yang aktif~~ — **sudah terjawab** (§2.6): Dual-Pipeline, N8N untuk fitur linear + Python-Native untuk fitur stateful. Yang masih perlu: **verifikasi independen** klaim ini (belum saya cek langsung ke `.env`/`agents/*.py`), dan konfirmasi apakah ada fitur yang keduplikasi di 2 pipeline sekaligus (§2.6).
8. **OpenAI di 6 workflow tersebut** — mau dikonsolidasi ke Gemini juga (konsisten sama keputusan awal), atau memang sengaja dibiarkan beda provider untuk fitur tertentu?
9. **Duplikasi Python-Native vs N8N** (§2.6) — CV Reviewer/Career Consultant kemungkinan ada implementasinya di 2 tempat (file `agents/*.py` DAN workflow n8n terpisah). Mana yang benar-benar dipanggil live oleh Streamlit? Perlu dicek supaya tidak salah maintain versi yang sudah "mati".

---

*Dokumen ini sudah disetujui (21 Juli 2026) dan menjadi acuan resmi project JobMatch AI — versi final yang menyatukan seluruh temuan audit, spesifikasi fitur, dan arsitektur target. Belum ada eksekusi/perubahan data dilakukan sejak persetujuan ini. Fase 0 (§10) adalah langkah eksekusi berikutnya; arsitektur target (§7B) adalah tujuan akhir setelah pertanyaan §13 terjawab.*
