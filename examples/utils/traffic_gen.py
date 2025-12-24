"""Traffic generation utilities for triggering alerts."""

import time
import requests
import threading
from .ui import print_progress


def generate_traffic_until_alert(app_url, prometheus_url, duration_sec=60):
    """
    Generate traffic to the application and wait for an alert to fire.
    
    Args:
        app_url: URL of the Flask application
        prometheus_url: URL of Prometheus server
        duration_sec: Maximum time to wait for alert
    
    Returns:
        Alert dict if found, None otherwise
    """
    
    print(f"Generating traffic for up to {duration_sec} seconds...")
    
    stop_flag = threading.Event()
    traffic_thread = threading.Thread(
        target=_traffic_worker,
        args=(app_url, stop_flag)
    )
    traffic_thread.daemon = True
    traffic_thread.start()
    
    alert = None
    start = time.time()
    
    while time.time() - start < duration_sec:
        elapsed = int(time.time() - start)
        print_progress(elapsed, duration_sec, prefix="Waiting for alert")
        
        try:
            r = requests.get(f"{prometheus_url}/api/v1/alerts", timeout=2)
            if r.status_code == 200:
                alerts = r.json().get('data', {}).get('alerts', [])
                firing = [a for a in alerts if a.get('state') == 'firing']
                if firing:
                    alert = firing[0]
                    print()
                    break
        except:
            pass
        
        time.sleep(5)
    
    stop_flag.set()
    traffic_thread.join(timeout=2)
    
    return alert


def _traffic_worker(app_url, stop_flag):
    """Background worker that generates HTTP traffic."""
    while not stop_flag.is_set():
        try:
            requests.get(f"{app_url}/api/v1/products", timeout=1)
            time.sleep(0.2)
            requests.post(f"{app_url}/api/v1/checkout", 
                         json={"items": []}, timeout=1)
        except:
            pass
        time.sleep(0.5)
