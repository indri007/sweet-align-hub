"""
Migration script: copy job data from local SQLite (data/jobs.db)
to the Aiven MySQL database defined in .env (DATABASE_URL).

Usage:
    python migrate_to_aiven.py

Requirements:
    - .env must contain DATABASE_URL pointing to your Aiven MySQL instance
    - ca.pem must be present in this folder (Aiven CA certificate)
    - Local SQLite file must exist at data/jobs.db
"""

import sqlite3
from pathlib import Path

import config
from database import DatabaseManager

LOCAL_SQLITE_PATH = Path(__file__).parent / "data" / "jobs.db"


def read_local_jobs() -> list[dict]:
    """Read all job rows from the local SQLite database."""
    if not LOCAL_SQLITE_PATH.exists():
        raise FileNotFoundError(f"Local SQLite DB not found at {LOCAL_SQLITE_PATH}")

    conn = sqlite3.connect(LOCAL_SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def main():
    if config.DATABASE_URL.startswith("sqlite"):
        print("DATABASE_URL masih menunjuk ke SQLite lokal.")
        print("Pastikan .env sudah diisi dengan DATABASE_URL Aiven MySQL sebelum migrasi.")
        return

    print(f"Target database: {config.DATABASE_URL.split('@')[-1]}")  # hide credentials in output

    print("Membaca data lokal dari SQLite...")
    local_rows = read_local_jobs()
    print(f"Ditemukan {len(local_rows)} baris di data/jobs.db")

    if not local_rows:
        print("Tidak ada data untuk dimigrasikan.")
        return

    print("Menghubungkan ke Aiven MySQL...")
    db = DatabaseManager()
    db.create_tables()

    existing_count = db.get_job_count()
    if existing_count > 0:
        confirm = input(
            f"Database Aiven sudah punya {existing_count} baris. "
            f"Lanjutkan menambah {len(local_rows)} baris baru? (y/n): "
        )
        if confirm.strip().lower() != "y":
            print("Migrasi dibatalkan.")
            return

    # Map SQLite rows back into the dict format expected by insert_jobs(),
    # which itself re-parses salary_raw -- so pass salary_raw as "salary".
    jobs_data = [
        {
            "job_title": row.get("job_title", ""),
            "company_name": row.get("company_name", ""),
            "location": row.get("location", ""),
            "work_type": row.get("work_type", ""),
            "salary": row.get("salary_raw", "None"),
            "job_description": row.get("job_description", ""),
            "_scrape_timestamp": row.get("scrape_timestamp", ""),
        }
        for row in local_rows
    ]

    print("Menulis data ke Aiven MySQL...")
    db.insert_jobs(jobs_data)

    final_count = db.get_job_count()
    print(f"Selesai. Total baris di Aiven sekarang: {final_count}")


if __name__ == "__main__":
    main()
