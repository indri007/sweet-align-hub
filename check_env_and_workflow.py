"""
check_env_and_workflow.py
1. Cek apakah .env sudah ada. Kalau belum, buat template kosong.
2. Tampilkan isi lengkap file n8n workflow (default: 1_cv_job_matcher.json).
"""

import json
import argparse
from pathlib import Path

ENV_TEMPLATE = """AIVEN_MYSQL_HOST=
AIVEN_MYSQL_PORT=3306
AIVEN_MYSQL_USER=
AIVEN_MYSQL_PASSWORD=
AIVEN_MYSQL_DB=
"""

INTERESTING_NODE_TYPES = [
    "n8n-nodes-base.httpRequest",
    "n8n-nodes-base.code",
    "n8n-nodes-base.function",
    "n8n-nodes-base.functionItem",
    "n8n-nodes-base.postgres",
    "n8n-nodes-base.mysql",
    "n8n-nodes-base.set",
    "n8n-nodes-base.webhook",
]


def check_or_create_env(root: Path):
    print("=" * 60)
    print("1. CEK / BUAT FILE .env")
    print("=" * 60)
    env_path = root / ".env"
    if env_path.exists():
        print(f"OK .env sudah ada di: {env_path}")
        content = env_path.read_text(encoding="utf-8")
        keys_present = [line.split("=")[0] for line in content.splitlines() if "=" in line]
        print(f"   Variabel terdeteksi: {', '.join(keys_present) if keys_present else '(kosong)'}")
        missing = [k for k in ["AIVEN_MYSQL_HOST", "AIVEN_MYSQL_USER", "AIVEN_MYSQL_PASSWORD", "AIVEN_MYSQL_DB"]
                   if k not in keys_present]
        if missing:
            print(f"   Variabel belum ada: {', '.join(missing)}")
    else:
        env_path.write_text(ENV_TEMPLATE, encoding="utf-8")
        print(f"Template .env dibuat di: {env_path}")
        print("Silakan isi kredensial Aiven MySQL manual di file tersebut.")


def find_workflow_file(root: Path, workflow_arg):
    if workflow_arg:
        candidate = root / workflow_arg
        if candidate.exists():
            return candidate
        print(f"File workflow tidak ditemukan di: {candidate}")
        return None
    matches = list(root.rglob("1_cv_job_matcher.json"))
    if not matches:
        print("Tidak menemukan file '1_cv_job_matcher.json'.")
        return None
    if len(matches) > 1:
        print(f"Ditemukan {len(matches)} file, pakai yang pertama:")
        for m in matches:
            print(f"  - {m}")
    return matches[0]


def show_workflow_detail(workflow_path: Path):
    print("\n" + "=" * 60)
    print(f"2. ISI LENGKAP WORKFLOW: {workflow_path.name}")
    print("=" * 60)
    try:
        data = json.loads(workflow_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Gagal parse JSON: {e}")
        return

    nodes = data.get("nodes", [])
    print(f"Total node: {len(nodes)}\n")

    for i, node in enumerate(nodes, 1):
        node_type = node.get("type", "unknown")
        node_name = node.get("name", "unnamed")
        is_interesting = node_type in INTERESTING_NODE_TYPES
        marker = "[SCRAPE?]" if is_interesting else "         "
        print(f"{marker} [{i}] {node_name}  ({node_type})")

        if is_interesting:
            params = node.get("parameters", {})
            for key in ["url", "method", "jsCode", "functionCode", "query", "operation", "path"]:
                if key in params:
                    value_str = str(params[key])
                    if len(value_str) > 500:
                        value_str = value_str[:500] + "... (dipotong)"
                    print(f"      {key}: {value_str}")
            print()

    print("=" * 60)
    print("Node bertanda [SCRAPE?] adalah kandidat sumber data job.")
    print("Kalau tidak ada httpRequest ke API/portal job eksternal,")
    print("scraping otomatis kemungkinan belum pernah diimplementasikan.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--workflow", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    print(f"Root project: {root}\n")

    check_or_create_env(root)
    workflow_path = find_workflow_file(root, args.workflow)
    if workflow_path:
        show_workflow_detail(workflow_path)


if __name__ == "__main__":
    main()
