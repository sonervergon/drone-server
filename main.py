
from dronekit import connect, VehicleMode
import time
import logging
import asyncio



logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

loop = asyncio.get_event_loop()

class RateLimiter:
    # MS
    last_sent = 0
    def __init__(self, freq = 1):
        self.frequency = freq

    def run(self, handler, name, value):
        if self.last_sent < time.time() - 1 / self.frequency:
            handler(name, value)
            self.last_sent = time.time()

def handle_change(attr_name, msg):
    logging.info("%s : %s", attr_name, msg)

async def run(attributes, messages):
    # Default local url  127.0.0.1:14550
    # Connect to the Vehicle.
    print("Connecting to vehicle")
    vehicle = connect("127.0.0.1:14550", wait_ready=True)

    for m in messages:
        print("Subscribing to MAVLink message " + m)
        rate_limiter = RateLimiter()
        vehicle.add_message_listener(m, lambda _self, name, value: rate_limiter.run(handle_change, name, value))

    for a in attributes:
        print("Subscribing to vehicle attribute " + a)
        rate_limiter = RateLimiter()
        vehicle.add_attribute_listener(a, lambda _self, name, value: rate_limiter.run(handle_change, name, value))

    

vehicle_attributes = ["heading"]
mavlink_messages = []

def main():
    try:
        loop.create_task(run(vehicle_attributes, mavlink_messages))
        loop.run_forever()
    except:
        logging.error("Event loop crashed")
        # main()

main()