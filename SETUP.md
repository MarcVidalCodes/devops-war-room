# Phase 1 Setup Guide

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+
- Git

## Initial Setup

### 1. Create feature branch

```bash
git checkout -b feature/buggy-ecommerce-api
```

### 2. Install dependencies locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov black flake8
```

### 3. Configure environment

```bash
cp .env.example .env
```

### 4. Run tests locally

```bash
pytest tests/ -v
```

### 5. Format and lint

```bash
black src/ tests/
flake8 src/ --max-line-length=120 --extend-ignore=E203,W503
```

## Running the Application

### Option 1: Docker Compose (Recommended)

```bash
docker-compose up -d
```

Wait 15 seconds for services to start, then verify:

```bash
curl http://localhost:5000/health
curl http://localhost:9090/-/healthy
curl http://localhost:3000/api/health
```

### Option 2: Local Development

```bash
export FLASK_ENV=development
python -m src.app.main
```

In another terminal, run Prometheus:
```bash
prometheus --config.file=monitoring/prometheus.yml
```

## Testing the Bugs

### 1. Trigger Random 5xx Errors

```bash
for i in {1..50}; do curl http://localhost:5000/api/v1/products; done
```

Watch Prometheus alerts at http://localhost:9090/alerts

### 2. Cause Memory Leak

```bash
for i in {1..200}; do 
  curl -X POST http://localhost:5000/api/v1/cart/user$i \
    -H "Content-Type: application/json" \
    -d '{"product_id":1,"quantity":1}'
done
```

Check metrics: http://localhost:5000/metrics (look for `memory_leak_objects`)

### 3. Trigger Slow Query Alert

```bash
for i in {1..10}; do 
  curl -X POST http://localhost:5000/api/v1/orders \
    -H "Content-Type: application/json" \
    -d '{"user_id":"user123"}' &
done
```

### 4. Exhaust Connection Pool

```bash
for i in {1..20}; do 
  curl -X POST http://localhost:5000/api/v1/checkout \
    -H "Content-Type: application/json" \
    -d '{"user_id":"user123"}' &
done
```

### 5. Run Full Load Test

```bash
chmod +x scripts/load_test.sh
./scripts/load_test.sh
```

## Accessing Dashboards

### Prometheus
- URL: http://localhost:9090
- View alerts: http://localhost:9090/alerts
- Query metrics: http://localhost:9090/graph

### Grafana
- URL: http://localhost:3000
- Username: admin
- Password: admin
- Dashboard: "E-commerce API Monitoring" (auto-provisioned)

## Verifying Metrics

Check all metrics are being collected:

```bash
curl http://localhost:5000/metrics | grep -E "(http_requests_total|http_errors_5xx|db_connection_pool_usage|memory_leak_objects|inventory_race_conditions)"
```

## Troubleshooting

### Services won't start

```bash
docker-compose down -v
docker-compose up -d
docker-compose logs -f
```

### Prometheus not scraping

```bash
curl http://localhost:9090/api/v1/targets
```

Verify target shows as "UP"

### Grafana dashboard not showing

1. Login to Grafana
2. Go to Configuration > Data Sources
3. Verify Prometheus is configured
4. Go to Dashboards > Browse
5. Find "E-commerce API Monitoring"

## Cleanup

```bash
docker-compose down -v
deactivate
```

## CI/CD Setup

### GitHub Actions

The CI pipeline will automatically run on:
- Push to `main`, `develop`, or `feature/**` branches
- Pull requests to `main` or `develop`

Pipeline stages:
1. Lint (Black, Flake8)
2. Unit Tests (pytest)
3. Docker Build
4. Integration Tests

### Creating a Pull Request

```bash
git add .
git commit -m "feat: Phase 1 - Buggy e-commerce API with monitoring"
git push origin feature/buggy-ecommerce-api
```

Then create PR on GitHub targeting `develop` branch.

## Success Criteria

Phase 1 is complete when:

- All tests pass locally
- Docker Compose starts all services successfully
- Load test triggers at least 3 different alert types
- Grafana dashboard shows all metrics panels
- CI pipeline passes on GitHub
- PR is merged to `develop`

## Next Phase

Phase 2 will add:
- LangChain-based MonitorAgent
- LangChain-based TriageAgent
- Prometheus query integration
- Agent logging and metrics
