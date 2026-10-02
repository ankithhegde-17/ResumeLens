"""Small, privacy-safe performance helpers for the Flask app."""
from collections import defaultdict, deque
from threading import Lock
import time


class PerformanceMetrics:
    """In-memory aggregates only: never request bodies, tokens, or resume text."""
    def __init__(self, recent=200):
        self.lock, self.values = Lock(), defaultdict(lambda: [0, 0.0])
        self.recent = deque(maxlen=recent)

    def record(self, name, seconds):
        with self.lock:
            count, total = self.values[name]
            self.values[name] = [count + 1, total + seconds]
            self.recent.append((name, round(seconds * 1000, 1)))

    def snapshot(self):
        with self.lock:
            return {name: {'count': count, 'total_ms': round(total * 1000, 1),
                           'average_ms': round(total * 1000 / count, 1)}
                    for name, (count, total) in self.values.items()}


class UserTTLCache:
    def __init__(self, ttl=30):
        self.ttl, self.lock, self.items = ttl, Lock(), {}

    def get(self, key):
        with self.lock:
            value = self.items.get(key)
            if not value or value[0] <= time.monotonic():
                self.items.pop(key, None)
                return None
            return value[1].copy()

    def put(self, key, value):
        with self.lock:
            self.items[key] = (time.monotonic() + self.ttl, dict(value))

    def invalidate(self, key):
        with self.lock:
            self.items.pop(key, None)
