# Agentic DevOps War Room

An autonomous AI agent system that monitors a live e-commerce application and attempts to diagnose and fix issues with human approval.

## Phase 1: Buggy E-commerce API with Monitoring

### Architecture

- **E-commerce API**: Flask REST API with intentional bugs
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Monitoring dashboard
- **Docker**: Containerization

### Intentional Bugs

1. **Random 5xx Errors**: 5% of product requests fail randomly
2. **Memory Leak**: Cart sessions are never released
3. **Slow Queries**: Order queries have 2-second delays
4. **Connection Pool Exhaustion**: Checkout doesn't release DB connections
5. **Race Conditions**: Inventory updates have timing issues

### Quick Start

1. Clone and setup:
```bash
git clone <repo-url>
cd devops-war-room
cp .env.example .env
```

2. Start services:
```bash
docker-compose up -d
```

3. Access services:
- API: http://localhost:5000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

4. Run load test:
```bash
chmod +x scripts/load_test.sh
./scripts/load_test.sh
```

### API Endpoints

- `GET /health` - Health check
- `GET /api/v1/products` - List products
- `GET /api/v1/products/<id>` - Get product
- `POST /api/v1/cart/<user_id>` - Add to cart
- `GET /api/v1/cart/<user_id>` - Get cart
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders/<user_id>` - Get orders
- `POST /api/v1/checkout` - Checkout
- `PUT /api/v1/inventory/<id>` - Update inventory
- `GET /api/v1/inventory` - Get inventory
- `GET /metrics` - Prometheus metrics

### Prometheus Alerts

- **HighErrorRate**: 5xx errors > 0.05/sec
- **SlowRequests**: 95th percentile > 2s
- **DatabasePoolExhaustion**: Pool usage >= 9/10
- **MemoryLeak**: Leaked objects > 100
- **InventoryRaceCondition**: Race conditions > 0.1/sec

### Development

Run tests:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov
pytest tests/
```

Run locally:
```bash
export FLASK_ENV=development
python -m src.app.main
```

### CI/CD

GitHub Actions pipeline includes:
- Linting (Black, Flake8)
- Unit tests
- Docker build
- Integration tests

### Next Steps

Phase 2 will add:
- MonitorAgent (LangChain)
- TriageAgent (LangChain)
- Prometheus integration for agents
