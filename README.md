# DevOps War Room: AI-Powered Incident Response

A simulated production environment with intentional bugs, monitored by an observability stack, and managed by autonomous AI agents that detect, triage, and diagnose incidents in real-time.

## 🚀 What It Does

1.  **Simulates a Broken App**: A Flask e-commerce API (`src/app`) with intentional bugs (memory leaks, database pool exhaustion, race conditions).
2.  **Monitors Everything**: Prometheus scrapes metrics; Grafana visualizes them.
3.  **Automated Response**:
    *   **Monitor Agent**: Detects firing alerts.
    *   **Triage Agent**: Investigates alerts by running specific PromQL queries to gather context.
    *   **Diagnostic Agent**: Uses Google Gemini (AI) to analyze the data, determine root causes, and recommend fixes.

## 🛠️ Architecture

*   **Application**: Python Flask (running in Docker).
*   **Infrastructure**: Docker Compose.
*   **Observability**: Prometheus (Metrics & Alerting), Grafana (Dashboards).
*   **AI/Automation**: Python Agents using LangChain & Google Gemini.

## ⚡ Quick Start

### 1. Prerequisites
*   Docker & Docker Compose
*   Python 3.11+
*   Google Gemini API Key (Free)

### 2. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set your API Key
export GOOGLE_API_KEY="your_api_key_here"
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
Wait about 30-60 seconds for alerts to fire, then run:
```bash
# Detects alerts, gathers metrics, and asks AI for a diagnosis
python examples/demo_diagnostic_agent.py
```

## 📂 Project Structure
*   `src/app`: The vulnerable Flask application.
*   `src/agents`: The Python agents (Monitor, Triage, Diagnostic).
*   `monitoring`: Prometheus and Grafana configuration.
*   `examples`: Demo scripts to run the agents.
