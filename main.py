
from dronekit import connect
from mqtt_connection import create_connection
from logger import init
from rate_limiter import RateLimiter
import asyncio
import json

logger = init()
loop = asyncio.get_event_loop()
client = create_connection('2MUTGA.Nn-1bw','0wGuSFcdjKn_qr_J', 'mqtt.ably.io')

handlers = {
    "location.global_frame": lambda d: { "lat": d.lat, "lon": d.lon, "alt": d.alt }
}

def handle_change(attr_name, msg):
    logger.info("%s : %s", attr_name, msg)
    payload = handlers[attr_name](msg) if handlers[attr_name] else msg
    data = { "name": attr_name, "data": payload }
    client.publish(attr_name, json.dumps(data), qos=0)

async def run(client, attributes, messages):
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

    

vehicle_attributes = ["location.global_frame"]
mavlink_messages = []

def main():
    try:
        loop.create_task(run(client, vehicle_attributes, mavlink_messages))
        loop.run_forever()
    except:
        logger.error("Event loop crashed")
        # main()

main()