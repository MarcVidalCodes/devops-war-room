# DevOps War Room: AI-Powered Incident Response

A simulated production environment with intentional bugs, monitored by an observability stack, and managed by autonomous AI agents that detect, triage, diagnose, and remediate incidents in real-time.

## Overview

1.  **Simulates a Broken App**: A Flask e-commerce API (`src/app`) with intentional bugs (memory leaks, database pool exhaustion, race conditions).
2.  **Monitors Everything**: Prometheus scrapes metrics; Grafana visualizes them.
3.  **Automated Response**:
    *   **Orchestrator**: Continuously queries Prometheus for firing alerts and coordinates the agent pipeline.
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

### 4. Start the System

```bash
# Start all services including the orchestrator
docker-compose up -d

# Wait for services to be ready (30 seconds)
sleep 30

# Pull Ollama model (first time only)
docker exec ollama ollama pull llama3

# Generate traffic to trigger alerts
bash examples/continuous_traffic.sh
```

In another terminal, follow the orchestrator logs to see the AI agents in action:

```bash
# Watch the orchestrator process alerts
docker logs -f war-room-orchestrator
```

The orchestrator continuously monitors for alerts and processes each one through the full agent pipeline. It handles deduplication to avoid processing the same alert multiple times.

## Project Structure
*   `src/app`: The vulnerable Flask application.
*   `src/agents`: The Python agents (Triage, Diagnostic, Remediation).
*   `src/orchestrator.py`: Main coordinator that queries Prometheus and runs all agents in sequence.
*   `src/integrations`: Clients for Prometheus and other tools.
*   `monitoring`: Prometheus and Grafana configuration.
*   `examples`: Scripts for generating traffic and triggering alerts.
*   `data/lancedb`: Local vector database for RAG memory.

## Resource Limits

All Docker services are configured with memory limits:
- **ecommerce-api**: 512MB (256MB reserved)
- **prometheus**: 1GB (512MB reserved)
- **grafana**: 512MB (256MB reserved)
- **ollama**: 4GB (2GB reserved) - needs more memory for LLM
- **orchestrator**: 1GB (512MB reserved)

These limits ensure the system runs efficiently on development machines while preventing any single service from consuming excessive resources.
