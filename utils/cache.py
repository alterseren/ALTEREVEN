# utils/cache.py - система кешування
import threading
import time
from typing import Dict, Any, Optional, Callable, Tuple


class Cache:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, ttl: int = 3600):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Cache, cls).__new__(cls)
                cls._instance.ttl = ttl
                cls._instance._cache = {}
            return cls._instance

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expires_at = self._cache[key]
            if time.time() < expires_at:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expiration = time.time() + (ttl if ttl is not None else self.ttl)
        self._cache[key] = (value, expiration)

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        self._cache.clear()

    def cached(self, key_prefix: str, ttl: Optional[int] = None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                key = f"{key_prefix}:{str(args)}:{str(kwargs)}"
                result = self.get(key)
                if result is None:
                    result = func(*args, **kwargs)
                    self.set(key, result, ttl)
                return result
            return wrapper
        return decorator