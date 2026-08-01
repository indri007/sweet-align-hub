# Hasil Evaluasi RAGAS — RAG Job Matching Pipeline

**Tanggal evaluasi:** 1 Agustus 2026
**Judge LLM:** OpenAI `gpt-4o-mini` (Gemini judge tidak dipakai karena kuota harian free-tier `gemini-3.6-flash` di project ini cuma 20 req/hari — habis untuk testing manual sebelum evaluasi berjalan)
**Embeddings evaluasi:** `sentence-transformers/all-MiniLM-L6-v2` (lokal, gratis — tidak dobel biaya dengan embedding production)
**Sample:** 5 CV sintetis (`evaluation/eval_dataset.py`) — software_engineer, data_scientist, marketing, hr, **graphic_designer** (baru ditambahkan, kategori dengan volume lowongan terbesar di dataset: 34 record)

## Ringkasan Skor

| Metrik | Rata-rata | Range per-CV |
|---|---|---|
| **Context Precision** | **1.000** | 1.00 di semua 5 CV |
| **Faithfulness** | 0.277 | 0.00 – 0.72 |
| **Answer Relevancy** | 0.282 | 0.20 – 0.42 |

## Interpretasi

**Retrieval (Qdrant + embedding): sangat baik.** Context Precision sempurna di semua sample — lowongan yang di-retrieve memang relevan terhadap CV. Bukan sumber masalah.

**Generation (`ai_summary` di `agents/rag_agent.py`): butuh perbaikan.** Faithfulness & Answer Relevancy rendah menunjukkan ringkasan yang dihasilkan AI sering menyertakan klaim yang tidak sepenuhnya didukung oleh data lowongan yang diambil, dan kurang secara langsung menjawab instruksi "rekomendasikan lowongan yang cocok". CV `graphic_designer` mencatat faithfulness terendah (0.00) — kandidat pertama untuk investigasi lanjutan.

## Perbaikan Teknis Selama Proses

1. **Bug kompatibilitas `ragas==0.3.9`:** class `HuggingfaceEmbeddings` bawaan ragas ternyata abstract/rusak di versi ini (dikonfirmasi bug publik: ragas issue #1806). Diganti dengan pola `LangchainEmbeddingsWrapper` yang stabil lintas versi.
2. **`EVAL_CVS` diperluas** dengan profil `graphic_designer` — kategori pekerjaan bervolume terbesar yang sebelumnya tidak terwakili di eval set.

## Rekomendasi Tindak Lanjut

- Perketat prompt di `agents/rag_agent.py` untuk `ai_summary`: tambahkan guardrail eksplisit anti-halusinasi (pola serupa dengan CV Generator yang sudah punya guardrail "dilarang fabrikasi") dan instruksi agar jawaban lebih langsung/ringkas menjawab task retrieval.
- Jalankan ulang evaluasi ini setelah revisi prompt untuk mengukur delta faithfulness/relevancy.
- Investigasi kasus `graphic_designer` (faithfulness 0.00) secara manual untuk pola halusinasi spesifik.
