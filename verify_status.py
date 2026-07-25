import os
import sys
from dotenv import load_dotenv
load_dotenv("/Users/jevin/Downloads/sweet-align-hub-main/.env", override=True)

RESULTS = []  # (nama_cek, status, detail)

def check(name):
    """Decorator sederhana buat catat hasil tiap pengecekan."""
    def wrapper(fn):
        try:
            status, detail = fn()
        except Exception as e:
            status, detail = "ERROR", f"Gagal menjalankan cek: {e}"
        RESULTS.append((name, status, detail))
    return wrapper


# ---------------------------------------------------------------
# 1. Cek jumlah lowongan: MySQL vs Qdrant (harus sama, §2.17)
# ---------------------------------------------------------------
@check("1. Sinkronisasi Job Data (MySQL vs Qdrant)")
def check_job_sync():
    from database import DatabaseManager
    from sqlalchemy import text
    import requests
    import os

    db = DatabaseManager()
    with db.engine.connect() as conn:
        # Cek jumlah job di MySQL berdasarkan keunikan doc_text
        query = text("""
            SELECT COUNT(*) FROM jobs
        """)
        mysql_count = conn.execute(query).scalar()

    q_url = "https://e4837ced-7c28-4e3a-a206-245ed54f7f20.sa-east-1-0.aws.cloud.qdrant.io"
    q_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZjcyNzUzOGItMjJkZi00YzhkLWIwOTQtMmRiNTg1NTVkM2Y4In0.EElU7AdqIqU1PNvFoYcjvvPKG2zv9ub5fgAKTF_jlDs"
    
    headers = {"api-key": q_key, "Content-Type": "application/json"}
    res = requests.get(f"{q_url}/collections/indonesian_jobs_gemini", headers=headers)
    
    if res.status_code == 200:
        qdrant_count = res.json().get("result", {}).get("points_count", 0)
    else:
        return "ERROR", f"Qdrant returned {res.status_code}"

    if mysql_count == qdrant_count:
        return "PASS", f"MySQL={mysql_count}, Qdrant={qdrant_count} — SUDAH SINKRON"
    else:
        gap = mysql_count - qdrant_count
        return "FAIL", f"MySQL={mysql_count}, Qdrant={qdrant_count} — SELISIH {gap} baris belum ter-ingest"


# ---------------------------------------------------------------
# 2. Cek collection hrd_knowledge sudah ada & terisi
# ---------------------------------------------------------------
@check("2. Collection hrd_knowledge (Leonardo)")
def check_hrd_knowledge():
    import requests
    import os
    
    q_url = "https://e4837ced-7c28-4e3a-a206-245ed54f7f20.sa-east-1-0.aws.cloud.qdrant.io"
    q_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZjcyNzUzOGItMjJkZi00YzhkLWIwOTQtMmRiNTg1NTVkM2Y4In0.EElU7AdqIqU1PNvFoYcjvvPKG2zv9ub5fgAKTF_jlDs"
    
    headers = {"api-key": q_key, "Content-Type": "application/json"}
    res = requests.get(f"{q_url}/collections", headers=headers)
    
    if res.status_code != 200:
        return "ERROR", f"Failed to get collections: {res.status_code}"
        
    collections = [c.get("name") for c in res.json().get("result", {}).get("collections", [])]

    if "hrd_knowledge" not in collections:
        return "FAIL", "Collection 'hrd_knowledge' BELUM ADA sama sekali"

    res_info = requests.get(f"{q_url}/collections/hrd_knowledge", headers=headers)
    info = res_info.json().get("result", {})
    points_count = info.get("points_count", 0)
    dim = info.get("config", {}).get("params", {}).get("vectors", {}).get("size", 0)
    
    if points_count == 0:
        return "FAIL", "Collection ada tapi KOSONG (0 points) — Leonardo tidak punya data"
    if dim != 768:
        return "FAIL", f"Dimensi vektor SALAH: {dim} (harusnya 768)"

    return "PASS", f"{points_count} points, dimensi 768 — Leonardo punya data"


# ---------------------------------------------------------------
# 3. Cek scoring_rubric — jumlah baris & apakah cv_analyzer_agent.py pakai ini
# ---------------------------------------------------------------
@check("3. Scoring Rubric (jumlah kriteria + dipakai analyzer atau tidak)")
def check_scoring_rubric():
    from database import DatabaseManager
    from sqlalchemy import text
    db = DatabaseManager()
    count = db.engine.connect().execute(text("SELECT COUNT(*) FROM scoring_rubric")).scalar()

    # Cek apakah cv_analyzer_agent.py punya jejak query ke scoring_rubric
    analyzer_path = "agents/cv_analyzer_agent.py"
    uses_db = False
    if os.path.exists(analyzer_path):
        with open(analyzer_path, "r", encoding="utf-8") as f:
            content = f.read()
            uses_db = "scoring_rubric" in content

    detail = f"{count} baris di database. cv_analyzer_agent.py {'SUDAH' if uses_db else 'BELUM'} query ke scoring_rubric."
    status = "PASS" if (count >= 14 and uses_db) else "FAIL"
    return status, detail


# ---------------------------------------------------------------
# 4. Cek pool API key Gemini — berapa yang benar-benar sehat
# ---------------------------------------------------------------
@check("4. Kesehatan API Key Gemini")
def check_gemini_keys():
    import re
    keys = []
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"GEMINI_API_KEY_?\d*\s*=\s*(.+)", line.strip())
                if m and m.group(1) and "your_key" not in m.group(1).lower():
                    keys.append(line.split("=")[0])

    if not keys:
        return "FAIL", "Tidak ada GEMINI_API_KEY_* ditemukan di .env"

    try:
        from google import genai
    except ImportError:
        return "ERROR", "Package google-genai belum terinstall, tidak bisa test key hidup/mati"

    healthy, dead = [], []
    for key_name in keys:
        val = os.environ.get(key_name)
        if not val:
            continue
        try:
            client = genai.Client(api_key=val)
            client.models.embed_content(model="gemini-embedding-001", contents="test")
            healthy.append(key_name)
        except Exception as e:
            dead.append(f"{key_name} ({str(e)[:60]})")

    detail = f"Sehat: {healthy} | Mati/bermasalah: {dead}"
    status = "PASS" if not dead else "FAIL"
    return status, detail


# ---------------------------------------------------------------
# 5. Cek webhook secret BUKAN placeholder
# ---------------------------------------------------------------
@check("5. Webhook Secret bukan placeholder")
def check_webhook_secret():
    if not os.path.exists(".env"):
        return "ERROR", "File .env tidak ditemukan"
    with open(".env", "r", encoding="utf-8") as f:
        content = f.read()

    if "N8N_WEBHOOK_SECRET" not in content:
        return "FAIL", "N8N_WEBHOOK_SECRET tidak ada di .env sama sekali"

    for line in content.splitlines():
        if line.strip().startswith("N8N_WEBHOOK_SECRET"):
            value = line.split("=", 1)[1].strip() if "=" in line else ""
            if value in ("password_rahasia_kamu", "", "your_secret_here"):
                return "FAIL", f"Masih placeholder: '{value}'"
            if len(value) < 20:
                return "FAIL", f"Secret terlalu pendek ({len(value)} char) — kemungkinan bukan hasil generate acak"
            return "PASS", f"Secret ada, panjang {len(value)} char (isi tidak ditampilkan demi keamanan)"

    return "ERROR", "Tidak bisa parse baris N8N_WEBHOOK_SECRET"


# ---------------------------------------------------------------
# 6. Cek EMBEDDING_MODEL bukan lagi "local"
# ---------------------------------------------------------------
@check("6. EMBEDDING_MODEL config")
def check_embedding_model():
    if not os.path.exists(".env"):
        return "ERROR", "File .env tidak ditemukan"
    with open(".env", "r", encoding="utf-8") as f:
        content = f.read()
    for line in content.splitlines():
        if line.strip().startswith("EMBEDDING_MODEL"):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value == "local":
                return "FAIL", "Masih di-set 'local' — bisa memicu bug dimensi 384 lagi"
            return "PASS", f"Di-set ke '{value}'"
    return "PASS", "Tidak ada baris EMBEDDING_MODEL eksplisit (pakai default Gemini, aman)"


# ---------------------------------------------------------------
# RUN ALL & PRINT SUMMARY
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("  VERIFIKASI STATUS JOBMATCH AI — HASIL DARI SUMBER LANGSUNG")
    print("=" * 70)
    print()

    for name, status, detail in RESULTS:
        icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️ "}.get(status, "❓")
        print(f"{icon} {name}")
        print(f"   Status : {status}")
        print(f"   Detail : {detail}")
        print()

    passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
    failed = sum(1 for _, s, _ in RESULTS if s == "FAIL")
    errors = sum(1 for _, s, _ in RESULTS if s == "ERROR")

    print("=" * 70)
    print(f"  RINGKASAN: {passed} PASS, {failed} FAIL, {errors} ERROR (dari {len(RESULTS)} cek)")
    print("=" * 70)

    if failed > 0 or errors > 0:
        sys.exit(1)
