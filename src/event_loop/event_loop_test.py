import unittest
import time
import asyncio
from unittest.mock import MagicMock
from event_loop import loop


async def serve(): 
    await asyncio.sleep(1)
    raise Exception("Server exited")

class ServerTest(unittest.TestCase):
    def setUp(self):
        self.task = MagicMock(side_effect=serve)

    def test_server_runs(self): 
        loop(self.task(), True)
        self.assertEqual(self.task.call_count, 1)



if __name__ == "__main__":
     unittest.main() # run all tests