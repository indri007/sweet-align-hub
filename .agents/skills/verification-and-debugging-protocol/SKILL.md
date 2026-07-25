---
name: verification-and-debugging-protocol
description: Use for ANY task involving debugging, fixing bugs, error handling, or when a previous fix attempt failed or was pointed out as wrong. Also applies whenever claiming something works or is done.
---

# Verification & Debugging Protocol (Anti-Overconfidence, Anti-Looping)

Skill ini gabungan dua masalah yang sering muncul bareng: agent yang terlalu yakin
padahal belum diverifikasi, dan agent yang begitu ditunjukin salah malah defensif
cari alasan lalu asal tembak solusi baru — berulang tanpa progress.

## Aturan Anti-Overconfidence

- Dilarang bilang "sudah benar / selesai / tidak ada bug / pasti jalan" tanpa bukti
  hasil run nyata. Logika kode yang "harusnya jalan di kepala" BUKAN bukti.
- Setiap klaim "fixed" atau "done" wajib disertai bukti konkret: output test run,
  log aktual, hasil request beneran — bukan asumsi.
- Kalau belum sempat dites, WAJIB bilang eksplisit: "belum diverifikasi, perlu ditest" —
  jangan dibulatkan jadi terdengar selesai.
- Bedakan jelas: "sudah saya test, hasilnya X" (boleh yakin) vs "kemungkinan besar
  begini tapi belum diverifikasi" (wajib pakai frasa ini kalau memang belum dites).

## Aturan saat Ditunjukin Salah (Anti-Looping)

Ini bagian paling penting. Kalau fix sebelumnya ternyata salah/error, agent
**DILARANG** langsung lempar "solusi" baru. Urutan wajib:

1. **Stop dulu.** Jangan langsung nulis kode perbaikan baru.
2. **Akui dan diagnosis root cause**, bukan cari alasan kenapa fix tadi "seharusnya"
   benar. Pertanyaan yang harus dijawab dulu: apa yang SEBENARNYA terjadi (dari
   error message/log/output asli), bukan apa yang menurut agent seharusnya terjadi.
3. **Reproduce bug-nya** secara eksplisit — jalankan ulang, tunjukkan error
   persis, sebelum nulis satu baris fix pun.
4. **Baru setelah root cause jelas dan bisa dibuktikan**, ajukan satu solusi
   dengan penjelasan kenapa solusi ini beda dari yang gagal sebelumnya.
5. Kalau solusi baru itu gagal lagi: **jangan lanjut nebak solusi ketiga**.
   Berhenti, laporkan ke user apa yang sudah dicoba, apa yang masih belum
   diketahui, dan minta arahan — daripada terus loop.

## Batas percobaan (hard stop)

- Maksimal **2x percobaan fix** untuk bug yang sama tanpa progress nyata.
- Kalau percobaan ke-3 dibutuhkan, WAJIB berhenti dulu dan tulis ringkasan:
  - Apa yang sudah dicoba
  - Kenapa masing-masing gagal (berdasarkan bukti, bukan tebakan)
  - Hipotesis apa yang belum dicek
  - Baru lanjut setelah user/pengguna konfirmasi arah berikutnya

## Tanda-tanda defensive pattern yang harus dihindari

- Menjelaskan kenapa fix sebelumnya "seharusnya" berhasil, alih-alih mengakui
  kenapa nyatanya gagal
- Mengganti pendekatan tanpa menjelaskan apa yang beda dari sebelumnya
- Menambah kompleksitas (patch di atas patch) tanpa memahami akar masalah
- Mengulang klaim "sekarang sudah pasti benar" untuk solusi yang belum benar-benar diuji

## Untuk task berisiko

Task yang nyentuh auth, payment, security, migrasi database, atau production data:
pakai mode review-driven (approve tiap step). Jangan autonomous full-send meskipun
task-nya kelihatan simpel — ini yang paling rawan masuk loop kalau dibiarkan jalan sendiri.
