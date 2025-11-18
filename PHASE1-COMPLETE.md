# Phase 1 Complete - Quick Start Guide

## What Just Happened

All services are now running in Docker:
- **E-commerce API**: http://localhost:5001
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## Open These URLs in Your Browser

### 1. Grafana Dashboard (Main monitoring view)
URL: http://localhost:3000
- Username: `admin`
- Password: `admin`
- Skip password change if prompted
- Go to: Dashboards → Browse → "E-commerce API Monitoring"

### 2. Prometheus (Metrics and alerts)
URL: http://localhost:9090
- Click "Alerts" at top to see alert rules
- Click "Graph" to query metrics

### 3. Test the API
URL: http://localhost:5001/api/v1/products

## You DON'T Need To:

1. **Manual Prometheus setup** - It's already configured in Docker
2. **Design the dashboard** - Already created and auto-loaded in Grafana
3. **Install Prometheus manually** - The one you downloaded isn't needed, use Docker version

## How to Trigger Bugs and See Alerts

### Quick Test - Run this in terminal:

```bash
for i in {1..100}; do 
  curl http://localhost:5001/api/v1/products > /dev/null 2>&1
  curl -X POST http://localhost:5001/api/v1/cart/user$i \
    -H "Content-Type: application/json" \
    -d '{"product_id":1,"quantity":1}' > /dev/null 2>&1
done
```

Wait 2 minutes, then check:
- Prometheus alerts: http://localhost:9090/alerts
- Grafana dashboard: http://localhost:3000

You should see:
- Random 5xx errors appearing
- Memory leak objects increasing
- Alerts firing in Prometheus

## What's Running in Docker Desktop

If you open Docker Desktop, you'll see 3 containers:
1. `ecommerce-api` - The buggy application
2. `prometheus` - Metrics collector
3. `grafana` - Dashboard

You can view logs by clicking on each container.

## Next Steps

1. Open the 3 URLs above in your browser
2. Run the test script to trigger some errors
3. Watch the Grafana dashboard update in real-time
4. See alerts fire in Prometheus

## To Stop Everything

```bash
docker-compose down
```

## To Restart Everything

```bash
docker-compose up -d
```

## Phase 1 Complete!

Everything is working. No manual Prometheus configuration needed. No dashboard design needed. It's all automated.

Next phase will add the AI agents.
