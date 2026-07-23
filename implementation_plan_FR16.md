# Implementasi FR-16: Agen 6 (Evaluator & Scoring)

Tujuan dari fase ini adalah mengimplementasikan **Agen 6** yang bertugas mengevaluasi seluruh jawaban kandidat di akhir sesi wawancara. Evaluasi akan didasarkan pada metodologi STAR (Situation, Task, Action, Result) dan menghasilkan skor serta *feedback* yang terstruktur.

## User Review Required

> [!IMPORTANT]
> Mohon tinjau skema JSON yang diusulkan untuk output Agen 6. Apakah ada dimensi khusus lain yang ingin Anda masukkan ke dalam penilaian (misalnya: *communication skill*, *confidence*, dsb) atau murni hanya skor kompetensi teknis/STAR?

## Open Questions

> [!WARNING]
> 1. Apakah *feedback* dari Agen 6 ini langsung ditampilkan kepada kandidat di layar Streamlit pada akhir wawancara, atau hanya disimpan di *backend* untuk dilihat HRD (FR-17)?
> 2. Berapa skala skor yang digunakan? (misalnya 1-5 atau 1-10)? Saya mengusulkan skala 1-5 sesuai standar SDM pada umumnya.

## Proposed Changes

### `agents/interview_agent.py`

#### [MODIFY] [interview_agent.py](file:///Users/jevin/Downloads/sweet-align-hub-backup-20260718/sweet-align-hub-extracted/agents/interview_agent.py)
Menambahkan fungsi `llm_generate_evaluation_score(session: InterviewSession) -> dict`:
- Fungsi ini merangkai seluruh riwayat tanya-jawab (`session.turns`) menjadi sebuah transkrip.
- Memanggil `chat_completion` (Gemini/OpenAI) dengan `system_prompt` khusus untuk Agen 6.
- Meminta LLM untuk membalas murni dalam format JSON.
- Menerapkan mekanisme proteksi/fallback `RuntimeError` jika API gagal (seperti pada FR-15).

### `agents/interview_agent_state.py`

#### [MODIFY] [interview_agent_state.py](file:///Users/jevin/Downloads/sweet-align-hub-backup-20260718/sweet-align-hub-extracted/agents/interview_agent_state.py)
Menambahkan fungsi `evaluate_interview(session: InterviewSession) -> dict`:
- Mengecek apakah wawancara sudah selesai (`is_completed`).
- Jika ya, memanggil `llm_generate_evaluation_score`.
- Menyimpan hasil skor ke dalam atribut `session.evaluation_result` agar bisa diakses oleh UI maupun untuk FR-17 kelak.

### `pages/step_e_interview.py`

#### [MODIFY] [step_e_interview.py](file:///Users/jevin/Downloads/sweet-align-hub-backup-20260718/sweet-align-hub-extracted/pages/step_e_interview.py)
- Ketika wawancara dinyatakan selesai (tidak ada `next_q`), panggil `evaluate_interview(session)`.
- Tampilkan hasil penilaian dan *feedback* kepada kandidat (jika disetujui di bagian *Open Questions*).

## Verification Plan

### Automated Tests
- Membuat `scripts/test_llm_quality_fr16.py` untuk menguji Agen 6 dengan transkrip *mock* (satu transkrip dengan jawaban bagus, satu transkrip dengan jawaban buruk) dan memverifikasi skor 1-5 yang diberikan masuk akal.

### Manual Verification
- Menjalankan Streamlit secara lokal, melakukan satu siklus wawancara penuh, menyelesaikan semua pertanyaan, dan melihat bagaimana hasil evaluasi akhir muncul di layar.
