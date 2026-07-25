---
name: skill-gap-analysis
description: Use when building or modifying the Skill Gap Analysis feature, or working with Qdrant vector search in the cvatsjob project.
---

# Skill Gap Analysis (Qdrant)

## Konsep
Membandingkan skill yang ada di CV (hasil parsing) dengan skill yang dibutuhkan
job description, pakai vector similarity search di Qdrant untuk mencari kecocokan/gap
yang tidak persis sama kata tapi mirip makna (misal "Node.js" vs "JavaScript backend").

## Yang harus diperhatikan
- Fitur ini masih tahap konsep/awal — cek dulu apakah sudah ada implementasi jalan
  sebelum bikin dari nol lagi
- Embedding buat query ke Qdrant sebaiknya di-cache per CV/job description, jangan
  generate ulang tiap kali user buka halaman yang sama

## Efisiensi token
- Proses embedding & similarity search di Qdrant tidak butuh Gemini — pisahkan mana
  yang perlu LLM (misal: menjelaskan gap dalam bahasa natural ke user) vs mana yang
  cukup vector math saja (mencari skill yang mirip)
- Kalau perlu LLM buat menjelaskan hasil gap analysis ke user, kirim hanya daftar
  gap yang sudah difilter (bukan seluruh raw data skill), biar prompt ringkas

## Testing sebelum bilang "selesai"
- Uji dengan job description yang skill-nya beda istilah tapi maknanya sama
- Pastikan hasil gap analysis masuk akal (bukan false positive skill yang sebenarnya ada)
