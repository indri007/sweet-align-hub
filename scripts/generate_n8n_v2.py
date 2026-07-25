import json
import copy
import uuid

def generate_id():
    return str(uuid.uuid4())

with open("n8n_workflows/AI_Job_Assistant_Latest.json", "r") as f:
    data = json.load(f)

data["name"] = "JobMatch AI V2 (Veronika & Leonardo)"

nodes = data["nodes"]
connections = data["connections"]

# Find the existing AI Agent, Qdrant, and MySQL to clone
ai_agent = next(n for n in nodes if n["name"] == "AI Agent")
qdrant = next(n for n in nodes if n["name"] == "Qdrant Vector Store")
mysql = next(n for n in nodes if n["name"] == "Execute a SQL query in MySQL")
llm = next(n for n in nodes if n["name"] == "Gemini Chat Model")

# Clone Veronika
veronika = copy.deepcopy(ai_agent)
veronika["id"] = generate_id()
veronika["name"] = "Veronika (CS Agent)"
veronika["position"] = [ai_agent["position"][0], ai_agent["position"][1] + 250]
veronika["parameters"]["text"] = "={{ $json.body.cs_query_veronika }}"
nodes.append(veronika)

# Clone Leonardo
leonardo = copy.deepcopy(ai_agent)
leonardo["id"] = generate_id()
leonardo["name"] = "Leonardo (CS Agent)"
leonardo["position"] = [ai_agent["position"][0], ai_agent["position"][1] + 500]
leonardo["parameters"]["text"] = "={{ $json.body.cs_query_leonardo }}"
nodes.append(leonardo)

# Clone Qdrant 2 (CS Memory)
qdrant2 = copy.deepcopy(qdrant)
qdrant2["id"] = generate_id()
qdrant2["name"] = "Qdrant 2 (CS Memory)"
qdrant2["position"] = [qdrant["position"][0], qdrant["position"][1] + 250]
qdrant2["parameters"]["qdrantCollection"]["value"] = "cs_long_term_memory"
qdrant2["parameters"]["qdrantCollection"]["cachedResultName"] = "cs_long_term_memory"
nodes.append(qdrant2)

# Clone Aiven 2 (Telemetry)
aiven2 = copy.deepcopy(mysql)
aiven2["id"] = generate_id()
aiven2["name"] = "Aiven 2 (Telemetry/Kafka)"
aiven2["position"] = [mysql["position"][0], mysql["position"][1] + 250]
aiven2["parameters"]["toolDescription"] = "Tool untuk menyimpan memory dan log CS ke Aiven 2."
nodes.append(aiven2)

# Vector Store Tool for Qdrant 2
vs_tool2 = copy.deepcopy(next(n for n in nodes if n["name"] == "Vector Store Tool"))
vs_tool2["id"] = generate_id()
vs_tool2["name"] = "CS Knowledge Tool"
vs_tool2["position"] = [vs_tool2["position"][0], vs_tool2["position"][1] + 250]
vs_tool2["parameters"]["description"] = "Cari knowledge base CS dan memory percakapan di Qdrant 2."
nodes.append(vs_tool2)

# Connect LLM to Veronika & Leonardo
connections["Gemini Chat Model"]["ai_languageModel"][0].extend([
    {"node": "Veronika (CS Agent)", "type": "ai_languageModel", "index": 0},
    {"node": "Leonardo (CS Agent)", "type": "ai_languageModel", "index": 0}
])

# Connect Webhook to Veronika & Leonardo
connections["Webhook"]["main"][0].extend([
    {"node": "Veronika (CS Agent)", "type": "main", "index": 0},
    {"node": "Leonardo (CS Agent)", "type": "main", "index": 0}
])

# Connect Aiven 2 and CS Knowledge Tool to Veronika & Leonardo
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

connections["Qdrant 2 (CS Memory)"] = {
    "ai_vectorStore": [
        [{"node": "CS Knowledge Tool", "type": "ai_vectorStore", "index": 0}]
    ]
}

connections["Gemini Embeddings"]["ai_embedding"][0].append(
    {"node": "Qdrant 2 (CS Memory)", "type": "ai_embedding", "index": 0}
)

with open("n8n_workflows/AI_Job_Assistant_V2_MultiAgent.json", "w") as f:
    json.dump(data, f, indent=2)

print("Generated AI_Job_Assistant_V2_MultiAgent.json")
