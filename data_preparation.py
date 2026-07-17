"""
Data Preparation Script
Processes jobs.jsonl into:
  1. SQLite database (structured data for SQL queries)
  2. ChromaDB vector store (text documents for RAG/semantic search)

Run this once to set up the data stores.
Usage: python data_preparation.py
"""

import json
import sys
from pathlib import Path

import config
from database import DatabaseManager, parse_salary
from vector_store import VectorStoreManager


def load_jsonl(filepath: Path) -> list[dict]:
    """Load JSONL file into list of dicts."""
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def prepare_rag_document(job: dict) -> str:
    """
    Create a combined text document for RAG from a job listing.
    Combines job_title, company_name, location, work_type, salary, and job_description.
    """
    parts = []
    parts.append(f"Job Title: {job.get('job_title', 'N/A')}")
    parts.append(f"Company: {job.get('company_name', 'N/A')}")
    parts.append(f"Location: {job.get('location', 'N/A')}")
    parts.append(f"Work Type: {job.get('work_type', 'N/A')}")

    salary = job.get("salary", "None")
    if salary and salary != "None":
        parts.append(f"Salary: {salary}")

    parts.append("")  # blank line separator
    parts.append(job.get("job_description", ""))

    return "\n".join(parts)


def setup_database(jobs_data: list[dict]) -> int:
    """Insert job data into SQLite database. Returns row count."""
    config.ensure_data_dir()
    db = DatabaseManager()
    db.create_tables()

    # Check if already populated
    existing_count = db.get_job_count()
    if existing_count > 0:
        print(f"  Database already has {existing_count} jobs. Skipping insert.")
        return existing_count

    db.insert_jobs(jobs_data)
    count = db.get_job_count()
    print(f"  Inserted {count} jobs into SQLite database.")
    return count


def setup_vector_store(jobs_data: list[dict]) -> int:
    """Insert job documents into ChromaDB. Returns document count."""
    config.ensure_data_dir()
    vs = VectorStoreManager()

    # Check if already populated
    existing_count = vs.get_collection_count()
    if existing_count > 0:
        print(f"  Vector store already has {existing_count} documents. Skipping insert.")
        return existing_count

    documents = []
    metadatas = []
    ids = []

    for i, job in enumerate(jobs_data):
        doc = prepare_rag_document(job)
        meta = {
            "job_title": job.get("job_title", ""),
            "company_name": job.get("company_name", ""),
            "location": job.get("location", ""),
            "work_type": job.get("work_type", ""),
            "salary": job.get("salary", "None"),
        }
        documents.append(doc)
        metadatas.append(meta)
        ids.append(f"job_{i}")

    print(f"  Embedding and inserting {len(documents)} documents into ChromaDB...")
    print("  (First run will download embedding model ~80MB, please wait...)")
    vs.add_documents(documents, metadatas, ids)
    count = vs.get_collection_count()
    print(f"  Inserted {count} documents into vector store.")
    return count


def main():
    print("=" * 60)
    print("  Data Preparation for Job Search App")
    print("=" * 60)

    # Load dataset
    print(f"\n[1/3] Loading dataset from {config.DATASET_PATH}...")
    if not config.DATASET_PATH.exists():
        print(f"  ERROR: Dataset not found at {config.DATASET_PATH}")
        sys.exit(1)

    jobs_data = load_jsonl(config.DATASET_PATH)
    print(f"  Loaded {len(jobs_data)} jobs.")

    # Quick stats
    titles = set(j.get("job_title") for j in jobs_data)
    with_salary = [j for j in jobs_data if j.get("salary") and j["salary"] != "None"]
    print(f"  Unique titles: {len(titles)}")
    print(f"  Jobs with salary: {len(with_salary)}")

    # Setup SQLite
    print("\n[2/3] Setting up SQLite database...")
    db_count = setup_database(jobs_data)

    # Setup ChromaDB
    print("\n[3/3] Setting up ChromaDB vector store...")
    vs_count = setup_vector_store(jobs_data)

    print("\n" + "=" * 60)
    print("  Data preparation complete!")
    print(f"  SQLite: {db_count} jobs")
    print(f"  ChromaDB: {vs_count} documents")
    print("=" * 60)


if __name__ == "__main__":
    main()
