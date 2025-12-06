# DevOps War Room: AI-Powered Incident Response

A simulated production environment with intentional bugs, monitored by an observability stack, and managed by autonomous AI agents that detect, triage, diagnose, and remediate incidents in real-time.

## Overview

1.  **Simulates a Broken App**: A Flask e-commerce API (`src/app`) with intentional bugs (memory leaks, database pool exhaustion, race conditions).
2.  **Monitors Everything**: Prometheus scrapes metrics; Grafana visualizes them.
3.  **Automated Response**:
    *   **Monitor Agent**: Detects firing alerts.
    *   **Triage Agent**: Investigates alerts by running specific PromQL queries to gather context.
    *   **Diagnostic Agent**: Uses a local Large Language Model (Llama 3 via Ollama) and Retrieval Augmented Generation (RAG) to analyze data, determine root causes, and recommend fixes based on past incidents.
    *   **Remediation Agent**: Generates actionable remediation plans (e.g., scaling commands, code patches) in structured JSON format.

## Architecture

*   **Application**: Python Flask (running in Docker).
*   **Infrastructure**: Docker Compose.
*   **Observability**: Prometheus (Metrics & Alerting), Grafana (Dashboards).
*   **AI/Automation**: Python Agents using LangChain, Ollama (Llama 3), and LanceDB (Vector Database for RAG).

## Quick Start

### 1. Prerequisites
*   Docker & Docker Compose
*   Python 3.11+
*   Ollama (installed and running locally)

### 2. Setup

First, ensure Ollama is running and pull the required models:
```bash
# Pull the LLM and the embedding model
ollama pull llama3
ollama pull nomic-embed-text
```

Install the Python dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run the Environment
Start the application and monitoring stack:
```bash
docker-compose up --build -d
```
*   **API**: http://localhost:5001
*   **Prometheus**: http://localhost:9090
*   **Grafana**: http://localhost:3000 (admin/admin)

### 4. Trigger Chaos & Run Agents
Open two terminal windows:

**Terminal 1: Generate Traffic (Trigger Alerts)**
```bash
# Sends traffic to trigger bugs like high error rates and latency
bash examples/continuous_traffic.sh
```

**Terminal 2: Run the AI Agent**
Wait about 30-60 seconds for alerts to fire, then run the remediation demo:
```bash
# Detects alerts, gathers metrics, diagnoses root cause, and proposes a fix
python examples/demo_remediation.py
```

## Project Structure
*   `src/app`: The vulnerable Flask application.
*   `src/agents`: The Python agents (Monitor, Triage, Diagnostic, Remediation).
*   `src/integrations`: Clients for Prometheus and other tools.
*   `monitoring`: Prometheus and Grafana configuration.
*   `examples`: Demo scripts to run the agents.
*   `data/lancedb`: Local vector database for RAG memory.
