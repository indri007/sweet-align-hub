import json
import copy
import uuid

def generate_id():
    return str(uuid.uuid4())

with open("n8n_workflows/AI_Job_Assistant_Latest.json", "r") as f:
    data = json.load(f)

data["name"] = "JobMatch AI V3 (Ultimate Enterprise Architecture)"

nodes = data["nodes"]
connections = data["connections"]

# Base Nodes
webhook = next(n for n in nodes if n["name"] == "Webhook")
webhook["name"] = "Streamlit App (Webhook Entry)"
webhook["position"] = [100, -200]

ai_agent = next(n for n in nodes if n["name"] == "AI Agent")
ai_agent["name"] = "Main Orchestrator Agent"
ai_agent["position"] = [450, -200]

mysql1 = next(n for n in nodes if n["type"] == "n8n-nodes-base.mySqlTool")
mysql1["name"] = "Aiven 1 (Primary SQL)"
mysql1["position"] = [600, -50]

qdrant1 = next(n for n in nodes if n["name"] == "Qdrant Vector Store")
qdrant1["name"] = "Qdrant 1 (Jobs Vector DB)"
qdrant1["position"] = [800, 250]

vs_tool1 = next(n for n in nodes if n["name"] == "Vector Store Tool")
vs_tool1["name"] = "HR Knowledge Tool"
vs_tool1["position"] = [800, 50]

gemini_model = next(n for n in nodes if n["name"] == "Gemini Chat Model")
gemini_model["position"] = [350, 50]

gemini_embed = next(n for n in nodes if n["name"] == "Gemini Embeddings")
gemini_embed["position"] = [750, 450]

# --- New Nodes ---

# Google Auth
google_auth = copy.deepcopy(mysql1)
google_auth["id"] = generate_id()
google_auth["name"] = "Google Auth Validator"
google_auth["type"] = "n8n-nodes-base.httpRequest"
google_auth["position"] = [300, -350]
google_auth["parameters"] = {"url": "https://oauth2.googleapis.com/tokeninfo", "method": "GET"}
nodes.append(google_auth)

# Connect Webhook -> Google Auth -> Main Agent
# Remove Webhook -> Main Agent connection
connections["Streamlit App (Webhook Entry)"] = {
    "main": [
        [{"node": "Google Auth Validator", "type": "main", "index": 0}]
    ]
}
connections["Google Auth Validator"] = {
    "main": [
        [
            {"node": "Main Orchestrator Agent", "type": "main", "index": 0},
            {"node": "Veronika (CS Agent)", "type": "main", "index": 0},
            {"node": "Leonardo (CS Agent)", "type": "main", "index": 0}
        ]
    ]
}

# Veronika
veronika = copy.deepcopy(ai_agent)
veronika["id"] = generate_id()
veronika["name"] = "Veronika (CS Agent)"
veronika["position"] = [450, 250]
veronika["parameters"]["text"] = "={{ $json.body.cs_query_veronika }}"
nodes.append(veronika)

# Leonardo
leonardo = copy.deepcopy(ai_agent)
leonardo["id"] = generate_id()
leonardo["name"] = "Leonardo (CS Agent)"
leonardo["position"] = [450, 500]
leonardo["parameters"]["text"] = "={{ $json.body.cs_query_leonardo }}"
nodes.append(leonardo)

# Aiven 2
aiven2 = copy.deepcopy(mysql1)
aiven2["id"] = generate_id()
aiven2["name"] = "Aiven 2 (Telemetry/Kafka)"
aiven2["position"] = [600, 250]
aiven2["parameters"]["toolDescription"] = "Simpan log ke Aiven 2."
nodes.append(aiven2)

# Qdrant 2
qdrant2 = copy.deepcopy(qdrant1)
qdrant2["id"] = generate_id()
qdrant2["name"] = "Qdrant 2 (CS Memory DB)"
qdrant2["position"] = [1000, 500]
qdrant2["parameters"]["qdrantCollection"]["value"] = "cs_memory"
nodes.append(qdrant2)

# CS Knowledge Tool
vs_tool2 = copy.deepcopy(vs_tool1)
vs_tool2["id"] = generate_id()
vs_tool2["name"] = "CS Knowledge Tool"
vs_tool2["position"] = [1000, 250]
vs_tool2["parameters"]["description"] = "Cari di Qdrant 2."
nodes.append(vs_tool2)

# Connect LLM
connections["Gemini Chat Model"]["ai_languageModel"][0].extend([
    {"node": "Veronika (CS Agent)", "type": "ai_languageModel", "index": 0},
    {"node": "Leonardo (CS Agent)", "type": "ai_languageModel", "index": 0}
])

# Connect Tools
connections["Aiven 2 (Telemetry/Kafka)"] = {
    "ai_tool": [
        [
            {"node": "Veronika (CS Agent)", "type": "ai_tool", "index": 0},
            {"node": "Leonardo (CS Agent)", "type": "ai_tool", "index": 0}
        ]
    ]
}

connections["CS Knowledge Tool"] = {
    "ai_tool": [
        [
            {"node": "Veronika (CS Agent)", "type": "ai_tool", "index": 0},
            {"node": "Leonardo (CS Agent)", "type": "ai_tool", "index": 0}
        ]
    ]
}

connections["Qdrant 2 (CS Memory DB)"] = {
    "ai_vectorStore": [
        [{"node": "CS Knowledge Tool", "type": "ai_vectorStore", "index": 0}]
    ]
}

# Fix Embeddings Connection
connections["Gemini Embeddings"]["ai_embedding"] = [
    [
        {"node": "Qdrant 1 (Jobs Vector DB)", "type": "ai_embedding", "index": 0},
        {"node": "Qdrant 2 (CS Memory DB)", "type": "ai_embedding", "index": 0}
    ]
]

# Map connections name changes
connections["Qdrant 1 (Jobs Vector DB)"] = connections.pop("Qdrant Vector Store")
connections["Aiven 1 (Primary SQL)"] = connections.pop("Execute a SQL query in MySQL")
connections["Main Orchestrator Agent"] = connections.pop("AI Agent")
connections["HR Knowledge Tool"] = connections.pop("Vector Store Tool")

with open("n8n_workflows/AI_Job_Assistant_V3_Ultimate.json", "w") as f:
    json.dump(data, f, indent=2)

print("Generated V3")
