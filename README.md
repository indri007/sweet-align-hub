# JobMatch AI: The Next-Generation Talent Alignment Platform 🚀

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-007AFF.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-App-FF0000.svg?style=for-the-badge&logo=streamlit&logoColor=white)](https://jobsmatch.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-FFE600.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/Build-Passing-98FB98.svg?style=for-the-badge)](https://github.com/indri007/sweet-align-hub)

**JobMatch AI** is an enterprise-grade, multi-agent artificial intelligence platform designed to bridge the chasm between top-tier talent and corporate recruitment demands. By leveraging Retrieval-Augmented Generation (RAG) and Distributed Microservices, we eliminate the friction in modern technical hiring.

---

## 📖 The Core Problem: The ATS "Black Box"

The modern recruitment pipeline is fundamentally broken. Every year, millions of highly qualified candidates are automatically rejected by rigid Applicant Tracking Systems (ATS) simply because their resumes lack specific keyword formatting. On the other side of the table, HR professionals spend up to 70% of their time manually sifting through unstructured CVs, leading to hiring bias and massive operational bottlenecks. 

**The consequence?** Companies lose top talent to competitors, and brilliant engineers remain unemployed due to algorithmic mismatches.

## 💡 Our Solution

**JobMatch AI** is built to solve this exact bottleneck. We do not rely on exact-match keyword searching. Instead, we developed a system that "understands" the semantic meaning behind a candidate's experience and mathematically aligns it with a company's true job requirements. 

We deliver an end-to-end recruitment lifecycle automation:
1. **Semantic Ingestion:** Extracting deep context from CVs.
2. **Precision Matching:** Using Cosine Similarity on high-dimensional vectors to find the perfect job fit.
3. **Automated Consulting:** Reconstructing the candidate's CV into an ATS-optimized format dynamically.
4. **Behavioral Simulation:** Conducting automated, stateful Mock Interviews with scoring matrixes.

---

## ⚡ Core Features

- **Multi-LLM Strategy Routing:** Dynamically routes inference workloads across Groq (Llama-3.3), Google Gemini 2.5 Flash, OpenRouter, and Mistral via an adapter pattern to guarantee 99.9% uptime and low latency.
- **Retrieval-Augmented Generation (RAG):** Integrates **Qdrant Cloud** vector databases for semantic matching, outperforming traditional boolean search methodologies.
- **Natural Language to SQL (NL2SQL):** Empowers recruiters and candidates to query structured relational data (salaries, job types) natively from **Aiven MySQL** using conversational English/Indonesian.
- **Asynchronous Telemetry:** Features **Aiven Kafka** pipelines for non-blocking event streaming, creating a robust Data Lake for future predictive analytics and employee retention forecasting.
- **Dual-Engine Orchestration:** Supports both high-speed Direct Python Choreography and configurable **N8N Webhook** Orchestrations for B2B enterprise workflows.

---

## 🛠️ System Architecture

Our platform utilizes a decoupled, cloud-native architecture:
- **Presentation Layer:** Streamlit (Client-side rendering, Session Management).
- **Security:** Native OAuth 2.0 with JWT encryption.
- **Database Layer:** Aiven MySQL (Structured), Qdrant (Vector/Semantic).
- **Data Streaming:** Confluent Kafka (C-based high-throughput streaming).

### 🤖 Advanced N8N Multi-Agent Architecture (V4)

JobMatch AI features an advanced **Multi-Agent Orchestration** system built on top of n8n. Instead of relying on a monolithic agent, the workload is distributed dynamically to specialized agents via an intelligent router to prevent fan-out collisions.

```mermaid
graph TD
    %% Styling
    classDef ui fill:#007AFF,stroke:#fff,stroke-width:2px,color:#fff;
    classDef router fill:#FFE600,stroke:#333,stroke-width:2px,color:#333;
    classDef agent fill:#FF0000,stroke:#fff,stroke-width:2px,color:#fff;
    classDef db fill:#98FB98,stroke:#333,stroke-width:2px,color:#333;
    
    A[Streamlit UI / Client]:::ui -->|HTTP POST Payload| B(Webhook Entrypoint):::router
    B --> C{Intelligent Router\nSwitch Node}:::router
    
    C -->|payload: cs_query_veronika| D[Veronika Agent\nSenior CS Manager]:::agent
    C -->|payload: cs_query_leonardo| E[Leonardo Agent\nSenior HRD/CS]:::agent
    C -->|default / CV upload| F[Main Orchestrator\nCore AI Agent]:::agent
    
    D -.->|Semantic Context| G[(Qdrant Vector DB)]:::db
    E -.->|Semantic Context| G
    F -.->|Semantic Context| G
    
    D -.->|Stateful Buffer| H[(Window Memory)]:::db
    E -.->|Stateful Buffer| H
    
    D ===>|LLM Inference| I([Groq Llama-3 / Gemini 2.5]):::ui
    E ===>|LLM Inference| I
    F ===>|LLM Inference| I
```

*For a detailed technical breakdown, please refer to [ARCHITECTURE.md](ARCHITECTURE.md).*

---

## 🚀 Quick Start & Installation

To deploy JobMatch AI locally for development or penetration testing, follow these engineering guidelines:

### 1. Prerequisites
- Python 3.10 or higher.
- Git & Docker (Optional for containerization).
- Valid SSL certificate (`ca.pem`) for Aiven Mutual TLS connections.

### 2. Environment Setup
Clone the repository and spin up a virtual environment:

```bash
git clone https://github.com/indri007/sweet-align-hub.git
cd sweet-align-hub
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
Install all required packages via pip:

```bash
pip install -r requirements.txt
```

### 4. Configuration (Secrets Management)
Create a `.env` file in the root directory. **Do not commit this file to version control.**

```env
# Database & Streaming
DATABASE_URL="mysql+pymysql://user:pass@host:port/db"
KAFKA_URI="host:port"
QDRANT_URL="https://your-qdrant-cluster.io"
QDRANT_API_KEY="your-api-key"

# AI Providers
GEMINI_API_KEY="your-gemini-key"
GROQ_API_KEY="your-groq-key"
LLM_PROVIDER="groq"
```

### 5. Launch the Application
Run the Streamlit server locally:

```bash
streamlit run app.py
```
Access the application dashboard at `http://localhost:8501`.

---

## 📈 Deployment (Streamlit Cloud)

This repository is configured for Continuous Deployment (CD) via GitHub Actions and Streamlit Cloud.
Any push to the `streamlit` branch will automatically trigger a rolling update.

1. Navigate to your Streamlit Cloud Dashboard.
2. In **App Settings > Secrets**, paste the contents of your TOML-formatted secrets.
3. The platform will automatically resolve dependencies and mount the TLS certificates required for Kafka and MySQL.

---

## 🤝 Contribution Guidelines
We welcome pull requests from the community. Please ensure that your code adheres to standard PEP-8 conventions and passes all RAGAS evaluation tests located in the `/evaluation` directory before submitting.

*Developed with precision for the Future of Work.*
