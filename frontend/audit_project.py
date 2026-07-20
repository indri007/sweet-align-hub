"""
audit_project.py
Cek project sebelum isi data scraping asli:
1. Cari file/folder terkait scraping, job, query, atau dataset.
2. Cek struktur tabel `job_listings` di MySQL Aiven (kalau sudah ada).
3. Cari file konfigurasi keyword/query pencarian job yang pernah dipakai.

Cara pakai:
    pip install pymysql python-dotenv --break-system-packages
    python audit_project.py
    python audit_project.py --root /path/ke/project   # default: folder saat ini
"""

import os
import re
import argparse
from pathlib import Path

import pymysql
from dotenv import load_dotenv

load_dotenv()

KEYWORDS_FILENAME = ["scrape", "job", "query", "dataset", "keyword"]
KEYWORDS_CONTENT = ["scrape", "beautifulsoup", "selenium", "requests.get", "n8n", "job_query", "search_keyword"]
IGNORE_DIRS = {"node_modules", ".git", "venv", "__pycache__", ".next", "dist", "build"}

MAX_PREVIEW_LINES = 15
MAX_FILE_SIZE = 300_000  # skip file gede biar nggak berat


def scan_related_files(root: Path):
    print("=" * 60)
    print("1. FILE/FOLDER TERKAIT SCRAPING, JOB, QUERY, DATASET")
    print("=" * 60)

    found_any = False
    for path in root.rglob("*"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".env.example", ".md"}:
            continue

        name_match = any(kw in path.name.lower() for kw in KEYWORDS_FILENAME)
        content_match = False

        if path.stat().st_size <= MAX_FILE_SIZE:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
                content_match = any(kw in text.lower() for kw in KEYWORDS_CONTENT)
            except Exception:
                text = ""
        else:
            text = ""

        if name_match or content_match:
            found_any = True
            rel_path = path.relative_to(root)
            reason = []
            if name_match:
                reason.append("nama file cocok")
            if content_match:
                reason.append("isi file mengandung keyword scraping")
            print(f"\n📄 {rel_path}  ({', '.join(reason)})")

            if text:
                lines = text.splitlines()
                preview = lines[:MAX_PREVIEW_LINES]
                for line in preview:
                    print(f"    {line}")
                if len(lines) > MAX_PREVIEW_LINES:
                    print(f"    ... ({len(lines) - MAX_PREVIEW_LINES} baris lagi)")

    if not found_any:
        print("Tidak ada file yang cocok ditemukan.")


def inspect_job_listings_table():
    print("\n" + "=" * 60)
    print("2. STRUKTUR TABEL job_listings DI MYSQL AIVEN")
    print("=" * 60)

    required_env = ["AIVEN_MYSQL_HOST", "AIVEN_MYSQL_USER", "AIVEN_MYSQL_PASSWORD", "AIVEN_MYSQL_DB"]
    missing = [k for k in required_env if not os.environ.get(k)]
    if missing:
        print(f"Skip: variabel .env belum lengkap ({', '.join(missing)}).")
        return

    try:
        conn = pymysql.connect(
            host=os.environ["AIVEN_MYSQL_HOST"],
            port=int(os.environ.get("AIVEN_MYSQL_PORT", 3306)),
            user=os.environ["AIVEN_MYSQL_USER"],
            password=os.environ["AIVEN_MYSQL_PASSWORD"],
            database=os.environ["AIVEN_MYSQL_DB"],
            ssl={"ssl": {}},
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as e:
        print(f"Gagal konek ke database: {e}")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES LIKE 'job_listings'")
            exists = cur.fetchone()
            if not exists:
                print("Tabel 'job_listings' belum ada di database. Akan dibuat otomatis saat ingest_jobs.py jalan.")
                return

            cur.execute("DESCRIBE job_listings")
            columns = cur.fetchall()
            print("Kolom yang sudah ada:")
            for col in columns:
                print(f"  - {col['Field']:<20} {col['Type']:<20} {'NULL' if col['Null']=='YES' else 'NOT NULL'}")

            cur.execute("SELECT DISTINCT query FROM job_listings ORDER BY query")
            existing_queries = [r["query"] for r in cur.fetchall()]
            print(f"\nQuery yang sudah pernah dipakai ({len(existing_queries)}):")
            for q in existing_queries:
                print(f"  - {q}")
    finally:
        conn.close()


def find_query_config(root: Path):
    print("\n" + "=" * 60)
    print("3. FILE KONFIGURASI KEYWORD/QUERY PENCARIAN JOB")
    print("=" * 60)

    pattern = re.compile(r'["\']?(query|keyword|search_term)s?["\']?\s*[:=]\s*[\[{]', re.IGNORECASE)
    found_any = False

    for path in root.rglob("*"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in {".py", ".js", ".ts", ".json", ".yaml", ".yml"}:
            continue
        if path.stat().st_size > MAX_FILE_SIZE:
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if pattern.search(text):
            found_any = True
            rel_path = path.relative_to(root)
            print(f"\n📄 {rel_path}")
            for i, line in enumerate(text.splitlines()):
                if pattern.search(line):
                    start = max(0, i - 1)
                    end = min(len(text.splitlines()), i + 3)
                    for j in range(start, end):
                        print(f"    {text.splitlines()[j]}")
                    print("    ---")

    if not found_any:
        print("Tidak ada file konfigurasi keyword/query yang ditemukan.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Folder root project yang mau di-scan")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    print(f"Scanning project di: {root}\n")

    scan_related_files(root)
    inspect_job_listings_table()
    find_query_config(root)

    print("\n" + "=" * 60)
    print("SELESAI. Gunakan hasil di atas untuk menyesuaikan field di scraped_jobs/*.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
