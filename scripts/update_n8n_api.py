import json
import requests

with open("n8n_workflows/AI_Job_Assistant_V3_Ultimate.json", "r") as f:
    data = json.load(f)

payload = {
    "name": data.get("name"),
    "nodes": data.get("nodes", []),
    "connections": data.get("connections", {}),
    "settings": {}
}

url = "https://n8n.kelasantai.online/api/v1/workflows/joc429PfquCLynfI"
headers = {
    "X-N8N-API-KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ODNiODdjYi0xNjg1LTRiOTQtYTJlYy05MjhlMWNiZDI5OGQiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNzE4ZDliZjgtMzgxYy00Y2M2LWFjYjctNTA5Njk3ZTFkOTc2IiwiaWF0IjoxNzg0MDE4MjY3LCJleHAiOjE3ODY1NTQwMDB9.f8-fwkwV1Ez0_41OfvEapbthQAwGv7zEWx5wLuPvM54",
    "Content-Type": "application/json"
}

resp = requests.put(url, json=payload, headers=headers)
print(resp.status_code, resp.text[:200])
