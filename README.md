<div align="center">

# 🎯 JobMatch AI
### Platform AI untuk Pencarian Kerja, Analisis CV, dan Simulasi Wawancara
*Dibangun khusus untuk Pasar Kerja Indonesia* 🇮🇩

<br/>

<a href="https://jobsmatch.streamlit.app/">
  <img src="assets/demo.webp" alt="JobMatch AI UI Demo Animation" width="800" style="border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2);">
</a>

<br/><br/>

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-jobsmatch.streamlit.app-00C7B7?style=for-the-badge&logo=streamlit&logoColor=white)](https://jobsmatch.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Gemini](https://img.shields.io/badge/Gemini_1.5_Flash-AI-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC244C?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)

**[📖 Baca PRD Lengkap](./PRD_JobMatch_AI.md)** &nbsp;&bull;&nbsp; **[🗂️ Lihat ERD Database](./ERD_JobMatch_AI.md)**

</div>

---

## 🧩 Kenapa Project Ini Dibuat?

Pasar kerja di Indonesia saat ini sangat kompetitif. Banyak talenta berbakat yang gagal ke tahap wawancara hanya karena resume mereka **tidak teroptimasi untuk sistem pelacakan pelamar (ATS)**, atau mereka kesulitan mencari lowongan yang benar-benar relevan dengan keahlian spesifik mereka.

**JobMatch AI** hadir untuk menjembatani kesenjangan tersebut. Kami memanfaatkan teknologi Generative AI terbaru untuk memberikan evaluasi objektif dan bimbingan yang terpersonalisasi. Mulai dari analisis kelayakan CV secara otomatis hingga simulasi wawancara mendalam, platform ini dirancang untuk bertindak sebagai **Konsultan Karier Pribadi 24/7** bagi setiap pencari kerja.

| ❌ Masalah yang Sering Terjadi | ✅ Solusi JobMatch AI |
|:---|:---|
| CV ditolak bot ATS karena format/keyword salah | **Skor ATS otomatis** + saran perbaikan konkret |
| Pencarian lowongan manual memakan waktu | **Pencarian Semantik** — deskripsikan dengan natural |
| Tidak ada sarana latihan wawancara profesional | **Simulasi HRD AI** berbasis *STAR method* |
| Pertanyaan berulang ke CS memakan waktu | **Chatbot Support 24/7** dengan *Knowledge Base* resmi |
| Feedback dari wawancara biasanya sangat generik | **Evaluasi AI Detail** per kategori kompetensi |

---

## ✨ Fitur Utama yang Mengubah Permainan

### 📄 1. CV Upload & ATS Scoring
Sistem langsung membaca PDF Anda, mengekstrak pengalaman, dan memberikan skor kelayakan berdasarkan standar HRD modern.
*(Penilaian didasarkan pada: Parsing 35% · Konten 60% · Match 5%)*

### 🔍 2. Semantic Job Search
Jangan lagi pusing memikirkan *keyword* kaku. Ketik saja, *"Saya lulusan desain grafis yang suka bikin logo dan ngerti marketing dikit"*, dan AI akan mencari kecocokan makna menggunakan **Qdrant Vector Database**.

### 🤖 3. Konsultan Karier & Chatbot CS AI
Bingung harus mulai dari mana? Tanyakan langsung ke AI. Chatbot dilatih khusus untuk memahami konteks resume Anda dan menjawab pertanyaan umum platform.

### 🎙️ 4. HRD Mock Interview (Fitur Baru!)
Simulasi wawancara *multi-turn* (tanya-jawab interaktif) menggunakan pendekatan metode STAR. AI akan menempatkan dirinya sebagai HRD yang sesungguhnya dan mengevaluasi jawaban Anda di akhir sesi, lengkap dengan transkrip yang disimpan di database Aiven MySQL.

---

## 🏗️ Arsitektur Sistem Berkelas Enterprise

Keseluruhan sistem ini dibangun menggunakan **Python-native murni**, membuang dependensi alat pihak ketiga seperti n8n untuk mendapatkan kecepatan maksimal, *state management* yang kuat, dan kontrol penuh atas *guardrail* (anti-halusinasi AI).

```mermaid
flowchart TD
    User(["👤 Pengguna"]) --> UI["🖥️ Streamlit App<br/>(Streamlit Cloud)"]

    UI --> Agents["🧠 AI Agents Layer<br/>(agents/*.py)"]

    Agents --> LLM{"🤖 LLM Provider"}
    LLM -->|utama| Gemini["✨ Google Gemini"]
    LLM -->|fallback| OpenAI["🔷 OpenAI"]

    Agents --> Vector["🔎 Qdrant Cloud<br/>(Semantic Search)"]
    Agents --> DB["🗄️ Aiven MySQL<br/>(Data Terstruktur)"]

    Vector --> Collections["📦 indonesian_jobs<br/>📦 hr_knowledge_base<br/>📦 interview_questions_bank<br/>📦 cs_knowledge_base"]
    DB --> Tables["📋 jobs · users<br/>📋 cv_analysis_results<br/>📋 hrd_transcripts"]

    classDef userStyle fill:#FFD166,stroke:#333,stroke-width:2px,color:#000
    classDef uiStyle fill:#06D6A0,stroke:#333,stroke-width:2px,color:#000
    classDef agentStyle fill:#118AB2,stroke:#333,stroke-width:2px,color:#fff
    classDef llmStyle fill:#8E75B2,stroke:#333,stroke-width:2px,color:#fff
    classDef dataStyle fill:#EF476F,stroke:#333,stroke-width:2px,color:#fff

    class User userStyle
    class UI uiStyle
    class Agents agentStyle
    class LLM,Gemini,OpenAI llmStyle
    class Vector,DB,Collections,Tables dataStyle
```

---

## 🎨 Material 3 Premium UI

Antarmuka **JobMatch AI** tidak hanya cerdas, tetapi juga **menawan secara visual**. Kami mendesain khusus *(custom CSS)* seluruh aplikasi menggunakan pedoman desain **Material 3 Dark Theme**:
- 🌌 **Glassmorphism:** Navigasi tembus pandang bergaya modern.
- 💊 **Pill-shaped Elements:** Sudut melengkung halus untuk pengalaman yang ramah pengguna.
- ✨ **Micro-animations:** Tombol *Pulse-glow* dan efek *hover* interaktif yang membuat aplikasi terasa sangat "hidup".

---

<div align="center">
  <b>Siap mendapatkan pekerjaan impian Anda berikutnya?</b><br><br>
  <a href="https://jobsmatch.streamlit.app/">
    <img src="https://img.shields.io/badge/Coba_Sekarang_Juga_🚀-00C7B7?style=for-the-badge&logo=streamlit" alt="Coba Sekarang">
  </a>
</div>
