#!/bin/bash

API_URL="http://localhost:5000/api/v1"
DURATION=300

echo "Starting load test for $DURATION seconds..."

end_time=$((SECONDS + DURATION))

while [ $SECONDS -lt $end_time ]; do
    curl -s "$API_URL/products" > /dev/null &
    curl -s "$API_URL/inventory" > /dev/null &
    curl -s -X POST "$API_URL/cart/user$RANDOM" -H "Content-Type: application/json" -d '{"product_id":1,"quantity":1}' > /dev/null &
    curl -s -X POST "$API_URL/orders" -H "Content-Type: application/json" -d '{"user_id":"user123"}' > /dev/null &
    curl -s -X POST "$API_URL/checkout" -H "Content-Type: application/json" -d '{"user_id":"user123"}' > /dev/null &
    
    sleep 0.1
done

echo "Load test complete"
