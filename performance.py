"""Small, privacy-safe performance helpers for the Flask app."""
from collections import defaultdict, deque
from threading import Lock
import time
import logging


class PerformanceMetrics:
    """In-memory aggregates only: never request bodies, tokens, or resume text."""
    def __init__(self, recent=200, diagnostics=False):
        self.lock, self.values = Lock(), defaultdict(lambda: [0, 0.0])
        self.recent = deque(maxlen=recent)
        self.diagnostics = diagnostics

    def record(self, name, seconds):
        with self.lock:
            count, total = self.values[name]
            self.values[name] = [count + 1, total + seconds]
            self.recent.append((name, round(seconds * 1000, 1)))
        if self.diagnostics:
            logging.getLogger('resumelens.performance').warning('stage=%s duration_ms=%.2f', name, seconds*1000)

    def snapshot(self):
        with self.lock:
            return {name: {'count': count, 'total_ms': round(total * 1000, 1),
                           'average_ms': round(total * 1000 / count, 1)}
                    for name, (count, total) in self.values.items()}
