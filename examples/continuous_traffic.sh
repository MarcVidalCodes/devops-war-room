#!/bin/bash

echo "=========================================="
echo "Continuous Traffic Generator"
echo "This will keep hitting the API to sustain high error rates"
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Run indefinitely until user stops
while true; do
    echo "[$(date +%H:%M:%S)] Sending burst of requests..."
    
    # Hit products endpoint (causes random 5xx errors)
    for i in {1..20}; do
        curl -s http://localhost:5001/api/v1/products > /dev/null &
    done
    
    # Hit cart endpoint (causes memory leak)
    for i in {1..10}; do
        curl -s -X POST http://localhost:5001/api/v1/cart \
            -H "Content-Type: application/json" \
            -d '{"product_id": 1, "quantity": 2}' > /dev/null &
    done
    
    # Hit checkout endpoint (exhausts connection pool)
    for i in {1..5}; do
        curl -s -X POST http://localhost:5001/api/v1/checkout \
            -H "Content-Type: application/json" \
            -d '{"user_id": 123}' > /dev/null &
    done
    
    # Hit inventory endpoint (causes race conditions)
    for i in {1..5}; do
        curl -s -X PUT http://localhost:5001/api/v1/inventory/1 \
            -H "Content-Type: application/json" \
            -d '{"quantity_change": -1}' > /dev/null &
    done
    
    # Wait for background jobs to complete
    wait
    
    # Small pause before next burst
    sleep 2
done
