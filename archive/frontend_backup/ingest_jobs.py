"""
ingest_jobs.py

Baca hasil scraping job (file JSON/CSV di sebuah folder), lalu simpan ke MySQL Aiven.

Aturan: maksimal 5 job per query, anti-duplikat berdasarkan URL.

Cara pakai:
    pip install pymysql python-dotenv

    # Buat file .env di folder yang sama:
    AIVEN_MYSQL_HOST=your-host.aivencloud.com
    AIVEN_MYSQL_PORT=xxxxx
    AIVEN_MYSQL_USER=avnadmin
    AIVEN_MYSQL_PASSWORD=xxxxx
    AIVEN_MYSQL_DB=defaultdb
    SCRAPED_FOLDER=./scraped_jobs

    python ingest_jobs.py
    python ingest_jobs.py --folder /path/lain
    python ingest_jobs.py --dry-run   # cuma tampilkan hasil parsing, tidak insert ke DB
"""

import os
import json
import csv
import argparse
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

import pymysql
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("ingest_jobs")

MAX_JOBS_PER_QUERY = 5
REQUIRED_FIELDS = ["query", "title", "company", "url"]
OPTIONAL_FIELDS = ["location", "salary", "work_type", "source", "description"]


def get_db_connection():
    """
    Parse DATABASE_URL (format: mysql+pymysql://user:pass@host:port/db?params)
    langsung dari .env -- tidak perlu AIVEN_MYSQL_HOST/PORT/USER/PASSWORD/DB terpisah.
    """
    from urllib.parse import urlparse

    database_url = os.environ["DATABASE_URL"]
    clean_url = database_url.replace("mysql+pymysql://", "mysql://", 1)
    parsed = urlparse(clean_url)

    return pymysql.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/").split("?")[0],
        ssl={"ssl": {}},  # Aiven wajib SSL
        cursorclass=pymysql.cursors.DictCursor,
    )


def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS job_listings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                query VARCHAR(255) NOT NULL,
                title VARCHAR(500) NOT NULL,
                company VARCHAR(255),
                location VARCHAR(255),
                salary VARCHAR(255),
                work_type VARCHAR(100),
                source VARCHAR(100),
                description TEXT,
                url VARCHAR(1000) NOT NULL,
                scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_url (url(500))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
    conn.commit()


def load_json_file(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("jobs") or data.get("results") or [data]
    return data if isinstance(data, list) else []


def load_csv_file(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_scraped_files(folder: Path):
    records = []
    files_found = 0
    for path in sorted(folder.glob("**/*")):
        if path.suffix.lower() == ".json":
            files_found += 1
            try:
                records.extend(load_json_file(path))
            except Exception as e:
                logger.warning(f"Gagal parse {path.name}: {e}")
        elif path.suffix.lower() == ".csv":
            files_found += 1
            try:
                records.extend(load_csv_file(path))
            except Exception as e:
                logger.warning(f"Gagal parse {path.name}: {e}")
    logger.info(f"Ditemukan {files_found} file, {len(records)} record mentah.")
    return records


def validate_record(rec: dict) -> bool:
    return all(rec.get(field) for field in REQUIRED_FIELDS)


def cap_per_query(records: list, max_per_query: int = MAX_JOBS_PER_QUERY):
    grouped = defaultdict(list)
    for rec in records:
        grouped[rec["query"]].append(rec)

    capped = []
    skipped_over_limit = 0
    for query, items in grouped.items():
        capped.extend(items[:max_per_query])
        skipped_over_limit += max(0, len(items) - max_per_query)

    return capped, skipped_over_limit, grouped


def insert_records(conn, records: list):
    inserted = 0
    duplicates = 0
    with conn.cursor() as cur:
        for rec in records:
            try:
                cur.execute(
                    """
                    INSERT IGNORE INTO job_listings
                        (query, title, company, location, salary, work_type, source, description, url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        rec.get("query"),
                        rec.get("title"),
                        rec.get("company"),
                        rec.get("location"),
                        rec.get("salary"),
                        rec.get("work_type"),
                        rec.get("source", "manual_import"),
                        rec.get("description"),
                        rec.get("url"),
                    ),
                )
                if cur.rowcount == 1:
                    inserted += 1
                else:
                    duplicates += 1
            except Exception as e:
                logger.error(f"Gagal insert '{rec.get('title')}': {e}")
    conn.commit()
    return inserted, duplicates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default=os.environ.get("SCRAPED_FOLDER", "./scraped_jobs"))
    parser.add_argument("--dry-run", action="store_true", help="Cuma parsing, tidak insert ke DB")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        logger.error(f"Folder tidak ditemukan: {folder}")
        return

    raw_records = load_scraped_files(folder)
    valid_records = [r for r in raw_records if validate_record(r)]
    invalid_count = len(raw_records) - len(valid_records)

    capped_records, skipped_over_limit, grouped = cap_per_query(valid_records)

    logger.info("=== Ringkasan Parsing ===")
    logger.info(f"Total record mentah   : {len(raw_records)}")
    logger.info(f"Record valid          : {len(valid_records)}")
    logger.info(f"Record invalid (skip) : {invalid_count}")
    logger.info(f"Query unik ditemukan  : {len(grouped)}")
    logger.info(f"Skip krn > {MAX_JOBS_PER_QUERY}/query   : {skipped_over_limit}")
    logger.info(f"Siap disimpan         : {len(capped_records)}")

    for query, items in grouped.items():
        logger.info(f"  - '{query}': {len(items)} ditemukan -> {min(len(items), MAX_JOBS_PER_QUERY)} disimpan")

    if args.dry_run:
        logger.info("Dry-run aktif, tidak ada yang disimpan ke database.")
        return

    if not capped_records:
        logger.warning("Tidak ada record valid untuk disimpan.")
        return

    conn = get_db_connection()
    try:
        ensure_table(conn)
        inserted, duplicates = insert_records(conn, capped_records)
        logger.info("=== Hasil Insert ke MySQL Aiven ===")
        logger.info(f"Berhasil disimpan (baru) : {inserted}")
        logger.info(f"Duplikat (dilewati)      : {duplicates}")
        logger.info(f"Selesai pada             : {datetime.now(timezone.utc).isoformat()}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
