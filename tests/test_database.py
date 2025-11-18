import pytest
from src.app.database import DatabaseConnectionPool

def test_pool_acquire_release():
    pool = DatabaseConnectionPool(pool_size=2, max_overflow=1)
    
    conn1 = pool.acquire()
    assert pool.active_connections == 1
    
    conn2 = pool.acquire()
    assert pool.active_connections == 2
    
    conn1.close()
    assert pool.active_connections == 1
    
    conn2.close()
    assert pool.active_connections == 0

def test_pool_exhaustion():
    pool = DatabaseConnectionPool(pool_size=1, max_overflow=0)
    
    conn1 = pool.acquire()
    
    with pytest.raises(Exception) as exc_info:
        conn2 = pool.acquire()
    
    assert "exhausted" in str(exc_info.value)
    conn1.close()

def test_connection_execute():
    pool = DatabaseConnectionPool(pool_size=5, max_overflow=5)
    conn = pool.acquire()
    
    result = conn.execute("SELECT * FROM test")
    assert result['success'] == True
    
    conn.close()
