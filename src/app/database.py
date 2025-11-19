import time
from threading import Lock
from src.app.config import Config
from src.app.metrics import db_connection_pool_usage


class DatabaseConnectionPool:
    def __init__(self, pool_size=5, max_overflow=5):
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.active_connections = 0
        self.lock = Lock()

    def acquire(self):
        with self.lock:
            if self.active_connections >= (self.pool_size + self.max_overflow):
                raise Exception("Database connection pool exhausted")
            self.active_connections += 1
            db_connection_pool_usage.set(self.active_connections)
        return MockConnection(self)

    def release(self):
        with self.lock:
            self.active_connections = max(0, self.active_connections - 1)
            db_connection_pool_usage.set(self.active_connections)


class MockConnection:
    def __init__(self, pool):
        self.pool = pool
        self.closed = False

    def execute(self, query):
        config = Config()
        if config.ENABLE_BUGS and "ORDER" in query:
            time.sleep(config.SLOW_QUERY_DELAY)
        return {"success": True, "rows": []}

    def close(self):
        if not self.closed:
            self.pool.release()
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


db_pool = DatabaseConnectionPool(
    pool_size=Config.DB_POOL_SIZE, max_overflow=Config.DB_MAX_OVERFLOW
)
