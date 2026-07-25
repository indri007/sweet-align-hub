# JobMatch AI (cvatsjob) — Project Context

## Ringkasan
Streamlit app untuk CV analysis dan ATS scoring. Bagian dari portofolio Indri
(developer + grad student). Deploy di Google Cloud Run.

## Stack
- Frontend/App: Streamlit (Python)
- LLM: `google-genai` SDK, model `gemini-2.5-flash`
- Database: Aiven MySQL
- Vector search: Qdrant
- Auth: Google OAuth via Streamlit native `st.login()`
- TTS: gTTS (dipakai di modul mock interview)
- Deploy: Google Cloud Run — GCP project `heaven-493814`
- Dev environment: Cloud Shell (user `ravipridh88`), Mac sekunder (user `jevin`)

## Konvensi kode
- Ikuti struktur modular hasil audit Tahap 3 (jangan taruh logic besar langsung di file utama Streamlit)
- Secrets **wajib** lewat Secret Manager, jangan pernah hardcode API key/token/password di kode atau commit
- Query ke MySQL wajib pakai parameterized query (hindari SQL injection)
- Kalau bikin fitur baru yang manggil Gemini, pertimbangkan biaya token — pakai prompt seringkas mungkin dan batasi output length

## Status audit (9 fase)
- Tahap 1–3: modularization — selesai
- Tahap 4: observability (logging, monitoring) — sedang berjalan
- Tahap 5–9: belum dimulai

## Known issues (jangan dianggap "sudah beres")
- Bug rendering PDF di beberapa kasus CV
- Akurasi hasil generate CV masih perlu ditingkatkan
- Modul mock interview butuh perbaikan flow
- SQL injection hardening masih berjalan, belum full-coverage

## Kapan pakai Skill mana
- Kerja di scoring/parsing CV → lihat skill `cv-ats-scoring`
- Kerja di modul interview 6-stage → lihat skill `mock-interview-module`
- Kerja di fitur Skill Gap Analysis / Qdrant → lihat skill `skill-gap-analysis`
- Kerja di secrets/SQLi/hardening → lihat skill `security-hardening`
- Debugging, fixing bug, atau klaim "sudah selesai/fixed" apapun → WAJIB lihat skill
  `verification-and-debugging-protocol` (anti-overconfidence, anti-looping)

## Aturan umum buat agent
- Jangan asumsikan credential aman untuk ditampilkan di log/output — selalu redact
- Sebelum ubah skema database, cek dulu apakah ada migration script yang harus dibuat
- Test manual dulu di local (pakai API key gratisan) sebelum saranin deploy ke Cloud Run production
- Tidak boleh klaim "done/fixed/pasti benar" tanpa mengikuti skill
  `verification-and-debugging-protocol` — ini berlaku di SEMUA task, bukan cuma yang berisiko
