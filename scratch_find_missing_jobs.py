import requests
import json
from database import DatabaseManager
from sqlalchemy import text

q_url = "https://e4837ced-7c28-4e3a-a206-245ed54f7f20.sa-east-1-0.aws.cloud.qdrant.io"
q_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZjcyNzUzOGItMjJkZi00YzhkLWIwOTQtMmRiNTg1NTVkM2Y4In0.EElU7AdqIqU1PNvFoYcjvvPKG2zv9ub5fgAKTF_jlDs"
headers = {"api-key": q_key, "Content-Type": "application/json"}

# get all from mysql
db = DatabaseManager()
with db.engine.connect() as conn:
    query = text("SELECT job_id FROM jobs")
    mysql_jobs = {row[0] for row in conn.execute(query).fetchall()}

print(f"MySQL jobs: {len(mysql_jobs)}")

# get all from qdrant (using scroll API)
qdrant_jobs = set()
offset = None
while True:
    payload = {"limit": 100, "with_payload": True, "with_vector": False}
    if offset:
        payload["offset"] = offset
    res = requests.post(f"{q_url}/collections/indonesian_jobs_gemini/points/scroll", headers=headers, json=payload)
    if res.status_code != 200:
        print(f"Error fetching from Qdrant: {res.status_code} {res.text}")
        break
    
    data = res.json().get("result", {})
    points = data.get("points", [])
    for p in points:
        payload = p.get("payload", {})
        job_id = payload.get("job_id")
        if job_id:
            qdrant_jobs.add(job_id)
            
    offset = data.get("next_page_offset")
    if not offset:
        break

print(f"Qdrant jobs: {len(qdrant_jobs)}")

missing = mysql_jobs - qdrant_jobs
print(f"Missing in Qdrant ({len(missing)}): {missing}")

