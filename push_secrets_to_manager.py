#!/usr/bin/env python3
"""
push_secrets_to_manager.py

Upload isi file backup .env (~/.env.daily-job-fetch.backup) ke Google Secret
Manager - supaya tidak ada lagi secret mentah tersimpan sebagai file .env di
project.

Mendukung ROTASI: kalau nilai sebuah key dipisah koma, misal:
    GEMINI_API_KEY=key_utama,key_cadangan_1,key_cadangan_2

maka akan dibuat 3 secret terpisah di Secret Manager:
    daily-job-fetch-gemini-api-key-1   (key_utama)
    daily-job-fetch-gemini-api-key-2   (key_cadangan_1)
    daily-job-fetch-gemini-api-key-3   (key_cadangan_2)

Runtime app (lihat secrets_manager.py) akan otomatis coba key-1 dulu, kalau
kena rate-limit/quota habis, otomatis pindah ke key-2, dst.

PENTING - jalankan di laptop Anda sendiri (bukan di Claude), karena butuh
`gcloud` CLI yang sudah login + library google-cloud-secret-manager.

Install dependency dulu (sekali saja):
    pip install google-cloud-secret-manager --break-system-packages

Cara pakai:
    python3 push_secrets_to_manager.py \\
        --env-file ~/.env.daily-job-fetch.backup \\
        --project heaven-493814 \\
        --prefix daily-job-fetch

Setelah berhasil, HAPUS file .env backup dari laptop (sudah tidak perlu):
    rm ~/.env.daily-job-fetch.backup
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from google.cloud import secretmanager
    from google.api_core.exceptions import AlreadyExists, NotFound
except ImportError:
    print("❌ Library belum terpasang. Jalankan dulu:")
    print("   pip install google-cloud-secret-manager --break-system-packages")
    sys.exit(1)


def parse_env_file(path: Path) -> dict[str, list[str]]:
    """Parse file .env sederhana: KEY=value1,value2,value3"""
    result = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not value:
            continue
        candidates = [v.strip() for v in value.split(",") if v.strip()]
        result[key] = candidates
    return result


def to_secret_id(prefix: str, env_key: str, index: int, total: int) -> str:
    """Ubah GEMINI_API_KEY -> daily-job-fetch-gemini-api-key-1 (kebab-case)."""
    kebab = re.sub(r"_", "-", env_key.lower())
    if total > 1:
        return f"{prefix}-{kebab}-{index}"
    return f"{prefix}-{kebab}"


def ensure_secret_exists(client, project: str, secret_id: str):
    parent = f"projects/{project}"
    secret_path = f"{parent}/secrets/{secret_id}"
    try:
        client.get_secret(name=secret_path)
        return secret_path, False  # sudah ada
    except NotFound:
        pass
    secret = client.create_secret(
        request={
            "parent": parent,
            "secret_id": secret_id,
            "secret": {"replication": {"automatic": {}}},
        }
    )
    return secret.name, True  # baru dibuat


def add_secret_version(client, secret_path: str, value: str):
    client.add_secret_version(
        request={
            "parent": secret_path,
            "payload": {"data": value.encode("utf-8")},
        }
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default="~/.env.daily-job-fetch.backup")
    parser.add_argument("--project", required=True)
    parser.add_argument("--prefix", default="daily-job-fetch")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Cuma print apa yang AKAN dibuat, tanpa benar-benar upload.",
    )
    args = parser.parse_args()

    env_path = Path(args.env_file).expanduser()
    if not env_path.exists():
        print(f"❌ File tidak ditemukan: {env_path}")
        sys.exit(1)

    parsed = parse_env_file(env_path)
    if not parsed:
        print("❌ Tidak ada key=value valid ditemukan di file .env ini.")
        sys.exit(1)

    print(f"Ditemukan {len(parsed)} key di {env_path}:")
    for key, values in parsed.items():
        rotasi_info = f" ({len(values)} versi untuk rotasi)" if len(values) > 1 else ""
        print(f"  - {key}{rotasi_info}")

    if args.dry_run:
        print("\n[DRY RUN] Secret ID yang akan dibuat:")
        for key, values in parsed.items():
            for i, _ in enumerate(values, start=1):
                print(f"  - {to_secret_id(args.prefix, key, i, len(values))}")
        return

    client = secretmanager.SecretManagerServiceClient()
    print(f"\nUpload ke Secret Manager project '{args.project}' ...")

    for key, values in parsed.items():
        for i, value in enumerate(values, start=1):
            secret_id = to_secret_id(args.prefix, key, i, len(values))
            secret_path, is_new = ensure_secret_exists(client, args.project, secret_id)
            add_secret_version(client, secret_path, value)
            status = "dibuat baru" if is_new else "versi baru ditambahkan"
            print(f"  ✅ {secret_id} - {status}")

    print(f"\n✅ Selesai. {len(parsed)} key berhasil dipindah ke Secret Manager.")
    print(f"\nLangkah selanjutnya:")
    print(f"  1. Update config.py untuk load dari Secret Manager (lihat secrets_manager.py)")
    print(f"  2. Kalau sudah yakin app jalan normal pakai Secret Manager, hapus backup lokal:")
    print(f"     rm {env_path}")


if __name__ == "__main__":
    main()
