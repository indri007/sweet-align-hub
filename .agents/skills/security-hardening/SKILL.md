---
name: security-hardening
description: Use when working on Secret Manager migration, SQL injection fixes, credential handling, or any security hardening task in the cvatsjob project.
---

# Security Hardening (cvatsjob)

## Status saat ini
- Migrasi ke Google Secret Manager: sedang berjalan (belum semua secret dipindah)
- SQL injection hardening: sedang berjalan (belum full-coverage semua query)

## Aturan wajib
- **Jangan pernah** tulis API key, token, atau password langsung di kode, log, atau
  chat/output — kalau nemu credential plaintext saat kerja di file manapun, tandai
  untuk dirotasi, jangan cuma dibiarkan
- Semua query ke Aiven MySQL wajib parameterized query — tidak boleh ada string
  concatenation langsung ke SQL
- Semua secret baru (API key baru, dsb) langsung didaftarkan ke Secret Manager,
  jangan taruh di `.env` yang ikut ke-commit

## Efisiensi & keamanan sekaligus
- Kalau nulis ulang kode yang manggil API key, cek dulu apakah key itu sudah
  seharusnya ambil dari Secret Manager — jangan generate kode baru yang malah
  hardcode lagi

## Testing sebelum bilang "selesai"
- Grep codebase buat memastikan tidak ada string yang kelihatan seperti API key/token
- Coba input SQL injection basic (`' OR 1=1 --` dsb) ke form yang terhubung ke query,
  pastikan tidak tembus
- Pastikan deploy ke Cloud Run tidak butuh env var berisi secret mentah
