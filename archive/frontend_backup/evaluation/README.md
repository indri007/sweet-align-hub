# Evaluasi RAG dengan Ragas

Mengukur kualitas pipeline job-matching (`agents/rag_agent.match_cv_to_jobs`)
menggunakan [Ragas](https://docs.ragas.io/). Ini adalah tool untuk developer/CI,
bukan fitur user-facing — tidak muncul di UI Streamlit.

## Kenapa Ragas?
`match_cv_to_jobs` itu RAG pipeline klasik: retrieval (vector search ke
ChromaDB/Qdrant) + generation (Gemini/OpenAI merangkum kenapa lowongan cocok).
Ragas mengukur dua hal yang sering jadi sumber bug diam-diam di RAG:
- **Apakah retrieval-nya relevan?** (`context_precision`)
- **Apakah AI generation-nya nyambung ke hasil retrieval, atau justru
  ngarang/halusinasi?** (`faithfulness`)
- **Apakah jawabannya benar-benar menjawab CV yang diberikan?** (`answer_relevancy`)

## Cara pakai
```bash
python evaluation/run_ragas_eval.py
python evaluation/run_ragas_eval.py --output results.json
```

Butuh `GEMINI_API_KEY` (atau `OPENAI_API_KEY`) sudah diisi di `.env` — dipakai
dua kali: sekali oleh app (lewat `llm_client`) untuk generate `ai_summary`,
sekali lagi oleh Ragas sebagai "judge" untuk menilai hasilnya. Vector store
(ChromaDB/Qdrant) juga harus sudah terisi (`python data_preparation.py`).

## Apa yang dievaluasi
`evaluation/eval_dataset.py` berisi 4 CV sintetis (Software Engineer, Data
Scientist, Marketing, HR) yang sengaja dipilih agar cocok dengan kategori
lowongan yang benar-benar ada di `dataset/jobs.jsonl`. Untuk tiap CV, script
menjalankan pipeline produksi apa adanya (bukan reimplementasi), lalu menilai
hasilnya dengan 3 metrik yang **tidak butuh ground truth** (jadi tidak perlu
label manual per lowongan):

| Metrik | Mengukur |
|---|---|
| `faithfulness` | Apakah narasi rekomendasi AI konsisten dengan isi lowongan yang di-retrieve, atau mengarang klaim yang tidak ada di sana |
| `answer_relevancy` | Apakah narasi rekomendasi benar-benar relevan dengan CV yang diberikan |
| `llm_context_precision_without_reference` | Apakah lowongan-lowongan yang di-retrieve relevan (dinilai LLM terhadap jawaban akhir) |

Skor 0–1, makin tinggi makin baik.

## Kenapa embedding evaluasi pakai model lokal (bukan Gemini/OpenAI)?
Supaya evaluasi tidak menambah biaya API embedding — pakai
`sentence-transformers` (`all-MiniLM-L6-v2`), model yang sama dengan default
embedder ChromaDB di app ini. LLM judge tetap pakai provider yang dikonfigurasi
di `.env` (Gemini secara default).

## Menambah CV evaluasi
Tambahkan entry baru ke `EVAL_CVS` di `evaluation/eval_dataset.py`. Usahakan
kategori pekerjaannya memang ada di `dataset/jobs.jsonl`, supaya skornya
bermakna (bukan cuma mengukur "tidak ada lowongan yang cocok").

## Kenapa tidak dijalankan otomatis di `entrypoint.sh` Docker?
Karena butuh API call berbayar ke LLM setiap kali container start, yang tidak
cocok untuk startup rutin. Jalankan manual atau sebagai step terpisah di CI:
```bash
docker compose run --rm app python evaluation/run_ragas_eval.py
```
