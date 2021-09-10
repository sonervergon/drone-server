import time


class RateLimiter:
    # ms
    last_sent = 0
    def __init__(self, freq = 1):
        self.frequency = freq

    def run(self, handler, name, value):
        if self.last_sent < time.time() - 1 / self.frequency:
            handler(name, value)
            self.last_sent = time.time()