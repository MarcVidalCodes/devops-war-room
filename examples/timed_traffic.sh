#!/bin/bash
echo "Running traffic for 90 seconds..."
end=$((SECONDS+90))

while [ $SECONDS -lt $end ]; do
    echo "[$(date +%H:%M:%S)] Sending burst..."
    for i in {1..20}; do curl -s http://localhost:5001/api/v1/products > /dev/null & done
    wait
    sleep 2
done
echo "Done."
