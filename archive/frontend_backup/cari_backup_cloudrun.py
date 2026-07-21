#!/usr/bin/env python3
"""
cari_backup_cloudrun.py

Mencari di laptop lokal (seluruh home directory, bukan cuma folder workspace
saat ini) file-file yang kemungkinan berhubungan dengan backup/export dari
deployment Cloud Run yang pernah menjalankan scraping job.

Cara pakai:
    python3 cari_backup_cloudrun.py

Jalankan skrip ini di LAPTOP ANDA (bukan di sandbox/container Claude),
karena skrip ini butuh akses langsung ke filesystem Anda dan (opsional)
ke gcloud/gsutil CLI yang sudah ter-autentikasi di mesin Anda.

Kriteria pencarian:
  1. Folder/file dengan nama mengandung: backup, export, cloudrun,
     cloud-run, cvatsjob (case-insensitive), di seluruh $HOME.
  2. File .json / .csv "besar" (>5KB) di Downloads/Documents/Desktop yang
     isinya mengandung indikasi data job scraping (field seperti "query",
     "job_title", "title", dst).
  3. File dump database (*.sql) di seluruh $HOME.
  4. Daftar isi Cloud Storage bucket lewat `gcloud storage ls` / `gsutil ls`
     (kalau CLI-nya terpasang & sudah login), untuk cek apakah backup-nya
     justru disimpan di GCS, bukan di disk lokal.

Hasil dicetak sebagai tabel: path, ukuran (human-readable), tanggal
modifikasi terakhir. Diurutkan dari yang paling baru dimodifikasi supaya
paling gampang mengenali backup mana yang dimaksud.
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()

# Folder/file yang selalu diabaikan supaya pencarian tidak lambat/berisik
IGNORE_DIR_NAMES = {
    "node_modules", ".git", ".cache", "venv", ".venv", "__pycache__",
    "Library", "AppData", ".Trash", ".npm", ".cargo", ".rustup",
}

NAME_KEYWORDS = ["backup", "export", "cloudrun", "cloud-run", "cvatsjob"]
CONTENT_KEYWORDS = ['"query"', '"job_title"', '"title"']

SEARCH_DIRS_FOR_DATA = [HOME / "Downloads", HOME / "Documents", HOME / "Desktop"]


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"


def should_skip_dir(dirpath: str) -> bool:
    parts = Path(dirpath).parts
    return any(p in IGNORE_DIR_NAMES for p in parts)


def walk_home():
    """Generator yang jalan sekali menyusuri $HOME, skip folder yang di-ignore."""
    for root, dirs, files in os.walk(HOME, topdown=True, onerror=lambda e: None):
        if should_skip_dir(root):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in IGNORE_DIR_NAMES and not d.startswith(".Trash")]
        yield root, dirs, files


def criterion_1_name_match():
    """Kriteria 1: nama folder/file mengandung salah satu keyword."""
    pattern = re.compile("|".join(re.escape(k) for k in NAME_KEYWORDS), re.IGNORECASE)
    hits = []
    for root, dirs, files in walk_home():
        for name in dirs + files:
            if pattern.search(name):
                hits.append(Path(root) / name)
    return hits


def criterion_2_data_files():
    """Kriteria 2: file .json/.csv besar di Downloads/Documents/Desktop yang
    isinya mengandung indikasi record job scraping."""
    hits = []
    for base in SEARCH_DIRS_FOR_DATA:
        if not base.exists():
            continue
        for root, dirs, files in os.walk(base, onerror=lambda e: None):
            if should_skip_dir(root):
                dirs[:] = []
                continue
            for fname in files:
                if not fname.lower().endswith((".json", ".csv")):
                    continue
                fpath = Path(root) / fname
                try:
                    if fpath.stat().st_size <= 5 * 1024:  # > 5KB saja
                        continue
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        # baca secukupnya saja, jangan load file raksasa penuh
                        content = f.read(200_000)
                    if any(kw in content for kw in CONTENT_KEYWORDS):
                        hits.append(fpath)
                except (OSError, PermissionError):
                    continue
    return hits


def criterion_3_sql_dumps():
    """Kriteria 3: file dump database (*.sql) di seluruh $HOME."""
    hits = []
    for root, dirs, files in walk_home():
        for fname in files:
            if fname.lower().endswith(".sql"):
                hits.append(Path(root) / fname)
    return hits


def criterion_4_gcs_buckets():
    """Kriteria 4: isi Cloud Storage lewat gcloud/gsutil, kalau CLI-nya ada."""
    results = {}
    for cmd in (["gcloud", "storage", "ls"], ["gsutil", "ls"]):
        exe = cmd[0]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            output = (proc.stdout or "") + (proc.stderr or "")
            results[" ".join(cmd)] = output.strip()
        except FileNotFoundError:
            results[" ".join(cmd)] = f"[{exe} tidak terpasang / tidak ada di PATH]"
        except subprocess.TimeoutExpired:
            results[" ".join(cmd)] = "[timeout menjalankan perintah]"
        except Exception as e:
            results[" ".join(cmd)] = f"[error: {e}]"
    return results


def print_file_table(title: str, paths):
    print(f"\n=== {title} ===")
    if not paths:
        print("  (tidak ditemukan)")
        return

    rows = []
    for p in sorted(set(paths)):
        try:
            st = p.stat()
            size = st.st_size if p.is_file() else sum(
                f.stat().st_size for f in p.rglob("*") if f.is_file()
            ) if p.is_dir() else 0
            mtime = datetime.fromtimestamp(st.st_mtime)
            rows.append((mtime, str(p), size))
        except (OSError, PermissionError):
            continue

    # urutkan: paling baru dimodifikasi di atas
    rows.sort(key=lambda r: r[0], reverse=True)

    for mtime, path_str, size in rows:
        print(f"  [{mtime:%Y-%m-%d %H:%M}] {human_size(size):>8}  {path_str}")


def main():
    print(f"Mencari di home directory: {HOME}")
    print("Proses ini bisa memakan waktu beberapa menit tergantung ukuran disk...\n")

    print("[1/4] Mencari nama folder/file mengandung: "
          f"{', '.join(NAME_KEYWORDS)} ...")
    hits1 = criterion_1_name_match()

    print("[2/4] Mencari file .json/.csv berisi data job scraping "
          "di Downloads/Documents/Desktop ...")
    hits2 = criterion_2_data_files()

    print("[3/4] Mencari file dump database (*.sql) ...")
    hits3 = criterion_3_sql_dumps()

    print("[4/4] Mengecek isi Cloud Storage bucket (gcloud/gsutil) ...")
    gcs_results = criterion_4_gcs_buckets()

    print_file_table(
        "1. Folder/file dengan nama backup/export/cloudrun/cloud-run/cvatsjob",
        hits1,
    )
    print_file_table(
        "2. File JSON/CSV berisi data job scraping (Downloads/Documents/Desktop)",
        hits2,
    )
    print_file_table(
        "3. File dump database (*.sql)",
        hits3,
    )

    print("\n=== 4. Isi Cloud Storage bucket (gcloud/gsutil) ===")
    for cmd_name, output in gcs_results.items():
        print(f"\n  $ {cmd_name}")
        if output:
            for line in output.splitlines():
                print(f"    {line}")
        else:
            print("    (kosong / tidak ada output)")

    total = len(set(hits1)) + len(set(hits2)) + len(set(hits3))
    print(f"\n\nTotal kandidat file/folder ditemukan (kriteria 1-3): {total}")
    print("Cek juga output kriteria 4 di atas untuk kemungkinan backup di GCS.")


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        print("Catatan: skrip ini ditulis dengan asumsi Unix-like home directory "
              "(~/Downloads dll). Di Windows, path Downloads/Documents/Desktop "
              "biasanya tetap terdeteksi otomatis lewat Path.home(), tapi jika "
              "tidak ketemu, sesuaikan SEARCH_DIRS_FOR_DATA secara manual.")
    main()
