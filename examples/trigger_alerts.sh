#!/bin/bash
#
# Trigger alerts for testing MonitorAgent
#
# This script generates traffic patterns that will trigger various alerts:
# - HighErrorRate: Many requests to trigger random 5xx errors
# - SlowRequests: Hits endpoints that have slow queries
# - DatabasePoolExhaustion: Rapid requests to exhaust connection pool
# - MemoryLeak: Creates cart sessions that leak memory
# - InventoryRaceCondition: Concurrent inventory updates

set -e

API_URL="http://localhost:5001/api/v1"

echo "=========================================="
echo "Triggering Alerts for MonitorAgent Demo"
echo "=========================================="

echo ""
echo "1. Triggering HighErrorRate alert..."
echo "   Sending 100 requests to trigger random 5xx errors..."
for i in {1..100}; do
    curl -s "$API_URL/products" > /dev/null 2>&1
done
echo "   Done. Error rate should trigger alert in 15-30 seconds."

echo ""
echo "2. Triggering MemoryLeak alert..."
echo "   Creating 60 cart sessions (leaks memory)..."
for i in {1..60}; do
    curl -s -X POST "$API_URL/cart" \
        -H "Content-Type: application/json" \
        -d "{\"user_id\": \"user_$i\", \"product_id\": 1, \"quantity\": 1}" \
        > /dev/null 2>&1
done
echo "   Done. Memory leak should trigger alert in 15-30 seconds."

echo ""
echo "3. Triggering DatabasePoolExhaustion alert..."
echo "   Rapid checkout requests (doesn't release connections)..."
for i in {1..10}; do
    curl -s -X POST "$API_URL/checkout" \
        -H "Content-Type: application/json" \
        -d "{\"user_id\": \"user_$i\"}" \
        > /dev/null 2>&1 &
done
wait
echo "   Done. Connection pool exhaustion should trigger alert in 15-30 seconds."

echo ""
echo "4. Triggering InventoryRaceCondition alert..."
echo "   Concurrent inventory updates..."
for i in {1..20}; do
    curl -s -X PUT "$API_URL/inventory/1" \
        -H "Content-Type: application/json" \
        -d "{\"quantity\": 100}" \
        > /dev/null 2>&1 &
done
wait
echo "   Done. Race condition should trigger alert in 15-30 seconds."

echo ""
echo "=========================================="
echo "All alerts triggered!"
echo "Watch MonitorAgent output for alert notifications."
echo "Alerts should appear within 30-60 seconds."
echo "=========================================="
