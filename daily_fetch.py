"""
Entry point for the daily JobMatch AI Cloud Run Job.
Rotates through ALL 10 top categories found in Dataset/jobs.jsonl
(1 category/day, full cycle every 10 days - no category skipped),
fetches jobs from JSearch (1 API call = 1 request against quota),
deduplicates against what's already in the database BEFORE trimming to
MAX_JOBS_PER_DAY, so the daily batch stays at 5 fresh jobs whenever
enough unique postings are available, then inserts into the SQL
database and the vector store (Gemini embeddings) - same pattern as
data_preparation.py / scraper.py.

Run manually for testing:
    python3 daily_fetch.py
"""

import datetime
from zoneinfo import ZoneInfo

from logger import get_logger
from metrics import track_duration, record_event
from jsearch_client import fetch_jobs
from database import DatabaseManager, Job
from vector_store import VectorStoreManager

logger = get_logger("daily_fetch")

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

MAX_JOBS_PER_DAY = 5

ROTATION_QUERIES = [
    "graphic designer jakarta",
    "data analyst jakarta",
    "product manager jakarta",
    "sales marketing jakarta",
    "software engineer jakarta",
    "digital marketing jakarta",
    "social media specialist jakarta",
    "digital marketing specialist jakarta",
    "hr generalist jakarta",
    "brand manager jakarta",
]


def _today_query() -> str:
    today = datetime.datetime.now(JAKARTA_TZ).date()
    day_index = today.toordinal() % len(ROTATION_QUERIES)
    return ROTATION_QUERIES[day_index]


def prepare_rag_document(job: dict) -> str:
    parts = [
        f"Job Title: {job.get('job_title', 'N/A')}",
        f"Company: {job.get('company_name', 'N/A')}",
        f"Location: {job.get('location', 'N/A')}",
        f"Work Type: {job.get('work_type', 'N/A')}",
    ]
    salary = job.get("salary", "None")
    if salary and salary != "None":
        parts.append(f"Salary: {salary}")
    parts.append("")
    parts.append(job.get("job_description", ""))
    return "\n".join(parts)


def _filter_out_duplicates(db: DatabaseManager, jobs: list[dict]) -> list[dict]:
    if not jobs:
        return jobs

    titles = [j["job_title"] for j in jobs]
    session = db.Session()
    try:
        existing_rows = (
            session.query(Job.job_title, Job.company_name)
            .filter(Job.job_title.in_(titles))
            .all()
        )
        existing_pairs = {(t, c) for t, c in existing_rows}
    finally:
        session.close()

    fresh = [j for j in jobs if (j["job_title"], j["company_name"]) not in existing_pairs]
    skipped = len(jobs) - len(fresh)
    if skipped:
        logger.info("Skipped duplicate jobs already in database", extra={"skipped": skipped})
    return fresh


def run():
    query = _today_query()

    with track_duration("daily_fetch"):
        try:
            jobs = fetch_jobs(query, country="id", num_pages=1)
        except Exception as e:
            logger.warning("RapidAPI JSearch failed, activating fallback to local dataset!", extra={"error": str(e)})
            import json
            import random
            jobs = []
            try:
                with open("dataset/jobs.jsonl", "r", encoding="utf-8") as f:
                    all_jobs = [json.loads(line) for line in f]
                random.shuffle(all_jobs)
                jobs = all_jobs[:MAX_JOBS_PER_DAY]
                logger.info("Fallback activated: Pulled 5 jobs from local dataset")
            except Exception as ex:
                logger.error("Fallback also failed", extra={"error": str(ex)})
                return

        if not jobs:
            logger.info("No jobs returned for query", extra={"query": query})
            record_event("daily_fetch_empty", query=query)
            return

        db = DatabaseManager()
        db.create_tables()

        jobs = _filter_out_duplicates(db, jobs)
        jobs = jobs[:MAX_JOBS_PER_DAY]
        logger.info(
            "Deduplicated and trimmed to daily cap",
            extra={"query": query, "kept": len(jobs), "cap": MAX_JOBS_PER_DAY},
        )

        if not jobs:
            logger.info("All jobs for today were already in the database", extra={"query": query})
            record_event("daily_fetch_all_duplicates", query=query)
            return

        try:
            db.insert_jobs(jobs)
            logger.info("Inserted jobs into SQL database", extra={"count": len(jobs)})
        except Exception as e:
            logger.error("SQL insert failed", extra={"error": str(e), "query": query})
            record_event("daily_fetch_failure", reason="sql_insert_error", query=query)
            raise

        try:
            vs = VectorStoreManager()
            documents, metadatas, ids = [], [], []
            # Ambil ID asli dari SQL supaya konsisten dengan skema "job_{id}"
            # yang dipakai data_preparation.py (mencegah data terduplikasi
            # di Qdrant akibat skema ID yang berbeda-beda).
            session = db.Session()
            inserted_rows = (
                session.query(Job)
                .filter(Job.job_title.in_([j["job_title"] for j in jobs]))
                .filter(Job.company_name.in_([j.get("company_name", "") for j in jobs]))
                .all()
            )
            title_to_id = {(r.job_title, r.company_name): r.id for r in inserted_rows}
            session.close()

            for job in jobs:
                documents.append(prepare_rag_document(job))
                metadatas.append({
                    "job_title": job.get("job_title", ""),
                    "company_name": job.get("company_name", ""),
                    "location": job.get("location", ""),
                    "work_type": job.get("work_type", ""),
                    "salary": job.get("salary", "None"),
                })
                job_key = (job.get("job_title", ""), job.get("company_name", ""))
                sql_id = title_to_id.get(job_key)
                ids.append(f"job_{sql_id}" if sql_id else f"daily_{datetime.date.today().isoformat()}_{job_key}")

            vs.add_documents(documents, metadatas, ids)
            logger.info("Inserted jobs into vector store", extra={"count": len(jobs)})
        except Exception as e:
            logger.error(
                "Vector store insert failed (SQL insert already succeeded)",
                extra={"error": str(e), "query": query},
            )
            record_event("daily_fetch_partial_failure", reason="vector_store_error", query=query)
            return

        record_event("daily_fetch_success", query=query, jobs_added=len(jobs))


if __name__ == "__main__":
    run()
