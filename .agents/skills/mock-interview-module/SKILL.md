---
name: mock-interview-module
description: Use when working on the 6-stage mock interview flow, Gemini-based question generation, or gTTS voice output in the cvatsjob project.
---

# Mock Interview Module (6-Stage Flow)

## Struktur flow
6 tahap wawancara simulasi, menggunakan `gemini-2.5-flash` untuk generate pertanyaan
dan evaluasi jawaban, gTTS untuk suara.

## Known issue
- Flow ini masih butuh perbaikan (belum stabil) — kalau nemu bug baru saat kerja
  di sini, catat di sini juga biar sesi berikutnya gak ngulang investigasi

## Efisiensi token
- Jangan kirim ulang seluruh riwayat percakapan interview ke Gemini tiap pertanyaan baru —
  kirim ringkasan konteks (jawaban sebelumnya + skor) bukan transkrip mentah penuh
- gTTS tidak butuh API berbayar — pastikan generate audio tidak lewat Gemini/API lain yang
  bayar per-request kalau gTTS lokal sudah cukup

## Testing sebelum bilang "selesai"
- Jalankan full 6 tahap end-to-end, cek transisi antar stage tidak nge-skip atau nge-freeze
- Cek output audio gTTS ke-generate dan ke-play dengan benar
- Verifikasi evaluasi jawaban dari Gemini konsisten dan relevan dengan pertanyaan yang diajukan
