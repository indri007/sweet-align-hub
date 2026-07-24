"""
Re-ingest dataset/jobs.jsonl ke Qdrant Cloud, di-embed pakai Gemini
(models/gemini-embedding-001), supaya kompatibel dengan node
"Google Gemini Embeddings" di workflow N8N (1_cv_job_matcher,
4_career_consultant).

Collection HASIL SCRIPT INI TERPISAH dari collection "indonesian_jobs"
yang sudah dipakai app Streamlit (yang itu pakai FastEmbed bawaan
Qdrant client, dimensinya beda). Jangan timpa collection lama.

Cara pakai (jalankan dari root folder project, misal ~/projects/jobmatch-restore/source-cvatsjob):

    pip install google-genai qdrant-client python-dotenv --break-system-packages
    python3 reingest_qdrant_gemini.py

Script ini baca GEMINI_API_KEY, QDRANT_URL, QDRANT_API_KEY dari file .env
(pakai python-dotenv) atau dari environment variable biasa.
"""

import json
import os
import sys
import time
import uuid

from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

DATASET_PATH = os.getenv("JOBS_DATASET_PATH", "dataset/jobs.jsonl")
COLLECTION_NAME = os.getenv("GEMINI_COLLECTION_NAME", "indonesian_jobs_gemini")
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
OUTPUT_DIM = int(os.getenv("GEMINI_EMBEDDING_DIM", "768"))  # 768/1536/3072 didukung model ini
BATCH_SIZE = 20  # jumlah dokumen per batch call ke Gemini + per upsert ke Qdrant
SLEEP_BETWEEN_BATCHES = 1.0  # detik, jaga2 rate limit


def fail(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def load_jobs(path: str) -> list[dict]:
    jobs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            jobs.append(json.loads(line))
    return jobs


def build_document_text(job: dict) -> str:
    """
    Gabungan teks untuk embedding, sesuai guideline dataset:
    job title + company name + job description.
    """
    parts = [
        job.get("job_title", ""),
        job.get("company_name", ""),
        job.get("job_description", ""),
    ]
    return "\n".join(p for p in parts if p)


def build_metadata(job: dict) -> dict:
    return {
        "job_title": job.get("job_title", ""),
        "company_name": job.get("company_name", ""),
        "location": job.get("location", ""),
        "work_type": job.get("work_type", ""),
        "salary": job.get("salary", ""),
        "job_description": job.get("job_description", "")[:2000],
        "scrape_timestamp": job.get("_scrape_timestamp", ""),
    }


def deterministic_id(key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, key))


def main():
    if not GEMINI_API_KEY:
        fail("GEMINI_API_KEY belum diset (cek .env kamu).")
    if not QDRANT_URL or not QDRANT_API_KEY:
        fail("QDRANT_URL / QDRANT_API_KEY belum diset (cek .env kamu).")
    if not os.path.exists(DATASET_PATH):
        fail(f"Dataset tidak ditemukan di '{DATASET_PATH}'. Set env JOBS_DATASET_PATH kalau lokasinya beda.")

    from google import genai
    from google.genai import types
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct

    gclient = genai.Client(api_key=GEMINI_API_KEY)
    qclient = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    jobs = load_jobs(DATASET_PATH)
    print(f"Loaded {len(jobs)} jobs dari {DATASET_PATH}")

    # (Re)create collection dengan dimensi yang sesuai
    existing = [c.name for c in qclient.get_collections().collections]
    if COLLECTION_NAME in existing:
        print(f"Collection '{COLLECTION_NAME}' sudah ada — akan di-recreate (data lama dihapus).")
        qclient.delete_collection(COLLECTION_NAME)

    qclient.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=OUTPUT_DIM, distance=Distance.COSINE),
    )
    print(f"Collection '{COLLECTION_NAME}' dibuat, dimensi={OUTPUT_DIM}")

    total = len(jobs)
    for start in range(0, total, BATCH_SIZE):
        batch = jobs[start:start + BATCH_SIZE]
        texts = [build_document_text(j) for j in batch]

        result = gclient.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=OUTPUT_DIM,
            ),
        )
        vectors = [emb.values for emb in result.embeddings]

        points = []
        for j, vec in zip(batch, vectors):
            key = f"{j.get('job_title','')}-{j.get('company_name','')}-{j.get('_scrape_timestamp','')}"
            points.append(PointStruct(
                id=deterministic_id(key),
                vector=vec,
                payload={
                    "document": build_document_text(j),
                    **build_metadata(j),
                },
            ))

        qclient.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"  upserted {min(start + BATCH_SIZE, total)}/{total}")
        time.sleep(SLEEP_BETWEEN_BATCHES)

    info = qclient.get_collection(COLLECTION_NAME)
    print(f"Selesai. Total points di '{COLLECTION_NAME}': {info.points_count}")


if __name__ == "__main__":
    main()
