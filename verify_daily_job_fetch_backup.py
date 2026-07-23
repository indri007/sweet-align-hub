#!/usr/bin/env python3
"""
verify_daily_job_fetch_backup.py

Merangkum & mengotomatiskan investigasi yang sudah dilakukan manual di terminal:
1. List semua source snapshot Cloud Run Job "daily-job-fetch" di GCS.
2. Download snapshot terbaru (timestamp terbesar) dan extract.
3. Validasi Dataset/jobs.jsonl: jumlah record, struktur field, rentang tanggal.
4. Deteksi kemungkinan data fallback/palsu dari scraper.py (bukan sekadar
   substring match nama perusahaan - dicek juga pola kalimat template-nya).
5. Cek potensi kebocoran kredensial (.env, AIVEN_SETUP.md, dsb) tanpa
   menampilkan isi rahasianya.

PENTING - jalankan ini di laptop Anda sendiri (Kiro / terminal Mac), BUKAN
di sandbox Claude, karena skrip ini memanggil `gcloud` CLI yang harus sudah
login ke akun & project GCP Anda (heaven-493814).

Cara pakai:
    python3 verify_daily_job_fetch_backup.py
    python3 verify_daily_job_fetch_backup.py --bucket run-sources-heaven-493814-asia-southeast2 \
        --job-path jobs/daily-job-fetch --project heaven-493814

Semua operasi di sini READ-ONLY terhadap project Anda (list, download ke
folder sementara, baca file) - tidak ada delete/overwrite ke GCS ataupun
ke database.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

DEFAULT_PROJECT = "heaven-493814"
DEFAULT_BUCKET = "run-sources-heaven-493814-asia-southeast2"
DEFAULT_JOB_PATH = "jobs/daily-job-fetch"

# Field yang wajib ada di tiap record hasil scraping (sesuai scraper.py / daily_fetch.py)
EXPECTED_FIELDS = {
    "job_title", "company_name", "location", "work_type",
    "salary", "job_description", "_scrape_timestamp",
}

# Pola kalimat template dari fallback generator di scraper.py - kalau match,
# record itu KEMUNGKINAN BESAR data sintetis, bukan hasil scraping asli.
FALLBACK_DESC_PATTERNS = [
    re.compile(r"Kami mencari .* berbakat untuk bergabung dengan tim kami", re.IGNORECASE),
    re.compile(r"Posisi .* di .* berlokasi di .*Membutuhkan keahlian dalam bidang", re.IGNORECASE),
]

FILES_THAT_MAY_HOLD_SECRETS = [".env", ".env.yaml", "AIVEN_SETUP.md"]


def run_cmd(cmd: list[str]) -> str:
    """Jalankan command, kembalikan stdout. Raise kalau gagal."""
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command gagal: {' '.join(cmd)}\n{proc.stderr.strip()}"
        )
    return proc.stdout


def check_gcloud_available():
    if shutil.which("gcloud") is None:
        print("❌ gcloud CLI tidak ditemukan di PATH. Install dulu / pastikan "
              "sudah login (`gcloud auth login`).")
        sys.exit(1)


def list_snapshots(bucket: str, job_path: str) -> list[str]:
    """List semua .zip snapshot untuk job ini, urut dari lama ke baru."""
    uri = f"gs://{bucket}/{job_path}/"
    print(f"[1/5] Listing snapshot di {uri} ...")
    out = run_cmd(["gcloud", "storage", "ls", uri])
    zips = [line.strip() for line in out.splitlines() if line.strip().endswith(".zip")]

    def sort_key(gs_uri: str) -> float:
        # nama file: <unix_timestamp>.<micros>-<uuid>.zip
        fname = gs_uri.rsplit("/", 1)[-1]
        try:
            return float(fname.split("-", 1)[0])
        except ValueError:
            return 0.0

    zips.sort(key=sort_key)
    print(f"      Ditemukan {len(zips)} snapshot.")
    return zips


def download_and_extract(gs_uri: str, workdir: Path) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    zip_name = gs_uri.rsplit("/", 1)[-1]
    zip_path = workdir / zip_name
    extract_dir = workdir / zip_name.replace(".zip", "")

    print(f"[2/5] Download snapshot terbaru: {zip_name}")
    run_cmd(["gcloud", "storage", "cp", gs_uri, str(zip_path)])

    print(f"      Extract ke {extract_dir} ...")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)

    return extract_dir


def find_dataset_file(extract_dir: Path) -> Path | None:
    candidates = list(extract_dir.rglob("*.jsonl"))
    if not candidates:
        return None
    # kalau ada beberapa, pilih yang di folder "Dataset" kalau ada
    for c in candidates:
        if "dataset" in c.parent.name.lower():
            return c
    return candidates[0]


def validate_dataset(jsonl_path: Path) -> dict:
    print(f"[3/5] Validasi dataset: {jsonl_path.relative_to(jsonl_path.parents[1])}")

    total = 0
    field_ok = 0
    timestamps = []
    fallback_suspects = []

    with open(jsonl_path, "r", encoding="utf-8", errors="ignore") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if EXPECTED_FIELDS.issubset(record.keys()):
                field_ok += 1

            ts = record.get("_scrape_timestamp")
            if ts:
                timestamps.append(ts)

            desc = record.get("job_description", "") or ""
            if any(p.search(desc) for p in FALLBACK_DESC_PATTERNS):
                fallback_suspects.append({
                    "line": line_no,
                    "job_title": record.get("job_title"),
                    "company_name": record.get("company_name"),
                })

    timestamps.sort()
    return {
        "total_records": total,
        "records_with_all_expected_fields": field_ok,
        "earliest_timestamp": timestamps[0] if timestamps else None,
        "latest_timestamp": timestamps[-1] if timestamps else None,
        "fallback_suspects": fallback_suspects,
    }


def check_secret_exposure(extract_dir: Path) -> list[str]:
    print("[4/5] Cek file yang berpotensi mengandung kredensial ...")
    found = []
    for fname in FILES_THAT_MAY_HOLD_SECRETS:
        matches = list(extract_dir.rglob(fname))
        for m in matches:
            found.append(str(m.relative_to(extract_dir)))
    return found


def print_report(zips, extract_dir, dataset_stats, dataset_path, secret_files):
    print("\n" + "=" * 60)
    print("LAPORAN VERIFIKASI BACKUP CLOUD RUN JOB: daily-job-fetch")
    print("=" * 60)

    print(f"\nTotal snapshot ditemukan di GCS : {len(zips)}")
    if zips:
        latest_name = zips[-1].rsplit("/", 1)[-1]
        ts_unix = float(latest_name.split("-", 1)[0])
        print(f"Snapshot terbaru               : {latest_name}")
        print(f"  (deploy time ~ {datetime.fromtimestamp(ts_unix):%Y-%m-%d %H:%M:%S})")
    print(f"Diekstrak ke                    : {extract_dir}")

    print("\n--- Dataset ---")
    if dataset_path is None:
        print("  Tidak ditemukan file .jsonl di snapshot ini.")
    else:
        print(f"  File               : {dataset_path.name}")
        print(f"  Total record       : {dataset_stats['total_records']}")
        print(f"  Field lengkap      : {dataset_stats['records_with_all_expected_fields']}"
              f" / {dataset_stats['total_records']}")
        print(f"  Rentang timestamp  : {dataset_stats['earliest_timestamp']} "
              f"s/d {dataset_stats['latest_timestamp']}")
        n_fallback = len(dataset_stats["fallback_suspects"])
        if n_fallback:
            print(f"  ⚠️  {n_fallback} record match pola kalimat fallback generator "
                  f"(perlu dicek manual, bisa jadi false positive):")
            for s in dataset_stats["fallback_suspects"][:10]:
                print(f"      - line {s['line']}: {s['job_title']} @ {s['company_name']}")
        else:
            print("  ✅ Tidak ada record yang match pola kalimat fallback generator.")

    print("\n--- Potensi kredensial di snapshot ---")
    if secret_files:
        print("  ⚠️  File berikut ditemukan (JANGAN dibagikan/commit ke git):")
        for f in secret_files:
            print(f"      - {f}")
        print("  Saran: reset password terkait & pastikan file ini ada di .gitignore.")
    else:
        print("  Tidak ada file .env/.env.yaml/AIVEN_SETUP.md di snapshot ini.")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--job-path", default=DEFAULT_JOB_PATH)
    parser.add_argument("--workdir", default=str(Path.home() / "Downloads" / "daily-job-fetch-verify"))
    parser.add_argument("--keep-files", action="store_true",
                         help="Jangan hapus zip & folder extract setelah selesai (default: dihapus).")
    args = parser.parse_args()

    check_gcloud_available()
    workdir = Path(args.workdir)

    zips = list_snapshots(args.bucket, args.job_path)
    if not zips:
        print("Tidak ada snapshot ditemukan. Cek nama bucket/job-path.")
        sys.exit(1)

    latest_zip_uri = zips[-1]
    extract_dir = download_and_extract(latest_zip_uri, workdir)

    dataset_path = find_dataset_file(extract_dir)
    dataset_stats = validate_dataset(dataset_path) if dataset_path else {}

    secret_files = check_secret_exposure(extract_dir)

    print_report(zips, extract_dir, dataset_stats, dataset_path, secret_files)

    if not args.keep_files:
        print("\n[5/5] Membersihkan file sementara (zip & folder extract) ...")
        zip_path = workdir / latest_zip_uri.rsplit("/", 1)[-1]
        if zip_path.exists():
            zip_path.unlink()
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        print(f"      Selesai. Folder kerja: {workdir}")
        print("      (Gunakan --keep-files kalau mau menyimpan hasil download.)")
    else:
        print(f"\nFile disimpan di: {extract_dir}")


if __name__ == "__main__":
    main()
