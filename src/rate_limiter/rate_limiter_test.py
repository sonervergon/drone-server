import unittest
import time
from unittest.mock import create_autospec
from rate_limiter import RateLimiter

def handler(name, value):
    pass


class RateLimiterTest(unittest.TestCase):
    def setUp(self):
        """Call before every test case."""
        self.limiter = RateLimiter(10)
        self.mock = create_autospec(handler)

    def test_is_only_called_once_when_called_very_fast(self):
        for x in range(10):
            self.limiter.run(self.mock, 'test', 1)
        self.mock.assert_called_with('test', 1)
        self.assertEqual(self.mock.call_count, 1)

    def test_is_limited_with_frequency_when_called_very_fast(self):
        for x in range(3):
            self.limiter.run(self.mock, 'test', 1)
            time.sleep(0.2)
        self.mock.assert_called_with('test', 1)
        self.assertEqual(self.mock.call_count, 3)



if __name__ == "__main__":
     unittest.main() # run all tests