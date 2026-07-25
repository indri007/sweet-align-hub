import json

with open("n8n_workflows/AI_Job_Assistant_V3_Ultimate.json", "r") as f:
    data = json.load(f)

# Define exact coordinates for a neat layout (Left to Right flow)
layout = {
    "Streamlit App (Webhook Entry)": [0, 350],
    "Google Auth Validator": [250, 350],
    
    # Shared Model
    "Gemini Chat Model": [400, 50],
    
    # Core Agents (Stacked vertically)
    "Main Orchestrator Agent": [550, 200],
    "Veronika (CS Agent)": [550, 450],
    "Leonardo (CS Agent)": [550, 700],
    
    # Tools for Main Agent
    "Aiven 1 (Primary SQL)": [850, 100],
    "HR Knowledge Tool": [850, 300],
    "Qdrant 1 (Jobs Vector DB)": [1150, 300],
    
    # Tools for CS Agents
    "Aiven 2 (Telemetry/Kafka)": [850, 550],
    "CS Knowledge Tool": [850, 750],
    "Qdrant 2 (CS Memory DB)": [1150, 750],
    
    # Shared Embeddings
    "Gemini Embeddings": [1150, 500]
}

# Apply layout
for node in data["nodes"]:
    name = node.get("name")
    if name in layout:
        node["position"] = layout[name]

with open("n8n_workflows/AI_Job_Assistant_V3_Ultimate.json", "w") as f:
    json.dump(data, f, indent=2)

print("Tidied up N8N layout")
