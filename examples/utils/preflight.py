"""Preflight checks for demo prerequisites."""

import requests
from .ui import print_check, print_warning


def run_preflight_checks():
    """Run all preflight checks. Returns True if all pass."""
    
    checks = [
        ("Prometheus", check_prometheus),
        ("Flask App", check_flask_app),
        ("Ollama Service", check_ollama),
        ("LLM Models", check_ollama_models),
    ]
    
    all_passed = True
    for name, check_func in checks:
        if check_func():
            print_check(f"[PASS] {name}")
        else:
            print_warning(f"[FAIL] {name}")
            all_passed = False
    
    return all_passed


def check_prometheus():
    """Check if Prometheus is reachable."""
    try:
        r = requests.get("http://localhost:9090/-/healthy", timeout=2)
        return r.status_code == 200
    except:
        return False


def check_flask_app():
    """Check if Flask app is running."""
    try:
        r = requests.get("http://localhost:5001/health", timeout=2)
        return r.status_code == 200
    except:
        return False


def check_ollama():
    """Check if Ollama service is running."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        return r.status_code == 200
    except:
        return False


def check_ollama_models():
    """Check if required Ollama models are installed."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        models = [m['name'] for m in r.json().get('models', [])]
        required = ['llama3', 'nomic-embed-text']
        return all(any(req in m for m in models) for req in required)
    except:
        return False
