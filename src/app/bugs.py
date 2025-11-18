import random
from src.app.config import Config

leaked_sessions = []

def trigger_random_error():
    config = Config()
    if config.ENABLE_BUGS and random.randint(1, 100) <= config.ERROR_RATE_PERCENT:
        raise Exception("Random 500 error triggered")

def memory_leak_cart_session(cart_data):
    config = Config()
    if config.ENABLE_BUGS:
        leaked_sessions.append({
            'cart_data': cart_data,
            'large_data': 'x' * 10000
        })

def cause_race_condition():
    config = Config()
    if config.ENABLE_BUGS:
        if random.randint(1, 100) <= 10:
            return True
    return False
