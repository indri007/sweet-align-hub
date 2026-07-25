import json
import requests
import re

with open("n8n_workflows/AI_Job_Assistant_V2_MultiAgent.json", "r") as f:
    text = f.read()

text = text.replace('"AI Agent"', '"Main Orchestrator Agent"')
text = text.replace('"Webhook"', '"Streamlit App (Webhook Entry)"')
text = text.replace('"Execute a SQL query in MySQL"', '"Aiven 1 (Primary SQL)"')
text = text.replace('"Qdrant Vector Store"', '"Qdrant 1 (Jobs Vector DB)"')
text = text.replace('"Vector Store Tool"', '"HR Knowledge Tool"')
text = text.replace('"JobMatch AI V2 (Veronika & Leonardo)"', '"JobMatch AI V3 (Ultimate Enterprise Architecture)"')

data = json.loads(text)

# Add Google Auth node
# ... actually, just pushing this fixed text without the Google Auth node is safer for the structure,
# wait, I can just use the V3 json I made earlier, and just do the string replace on the original V3 file!

with open("n8n_workflows/AI_Job_Assistant_V3_Ultimate.json", "r") as f:
    v3_text = f.read()

v3_text = v3_text.replace('"AI Agent"', '"Main Orchestrator Agent"')
v3_text = v3_text.replace('"Webhook"', '"Streamlit App (Webhook Entry)"')
v3_text = v3_text.replace('"Execute a SQL query in MySQL"', '"Aiven 1 (Primary SQL)"')
v3_text = v3_text.replace('"Qdrant Vector Store"', '"Qdrant 1 (Jobs Vector DB)"')
v3_text = v3_text.replace('"Vector Store Tool"', '"HR Knowledge Tool"')

data = json.loads(v3_text)

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

# save it back
with open("n8n_workflows/AI_Job_Assistant_V3_Ultimate.json", "w") as f:
    json.dump(data, f, indent=2)

