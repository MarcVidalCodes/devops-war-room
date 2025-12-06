#!/bin/bash
echo "Running traffic for 300 seconds..."
end=$((SECONDS+300))

while [ $SECONDS -lt $end ]; do
    echo "[$(date +%H:%M:%S)] Sending burst..."
    for i in {1..5}; do curl -s http://localhost:5001/api/v1/products > /dev/null & done
    wait
    sleep 1
done
echo "Done."
