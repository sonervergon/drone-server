#!/usr/bin/env python3.7
"""
Based on implementation here: https://roguelynn.com/words/asyncio-testing/
to achieve concurrency and Exception tolerance.
"""


# Feature dependencies
from dronekit import connect
import paho.mqtt.client as mqtt
from load_env import get
from rate_limiter.rate_limiter import RateLimiter
from service.asset_data_point_handlers import handlers
from service.check_internet import check_internet_connection

# Service dependencies
import asyncio
import logging
import random
import signal
import time
import string
import attr  # attrs

username = get("username")
password = get("password")
host = get("host")
port = get("port")
env = get("env")
asset_data = get("asset_data")
asset_host_name = get("asset_host_name")
asset_host_id = get("asset_host_id")
asset_tcp_endpoint = get("asset_tcp_endpoint")

instance = f"{asset_host_name}-{asset_host_id}"

asset_data_points = asset_data.split(",") if asset_data else []

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s.%(msecs)d, {asset_host_id} %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


@attr.s
class PubSubMessage:
    instance_name = attr.ib()
    data = attr.ib()
    saved = attr.ib(repr=False, default=False)
    acked = attr.ib(repr=False, default=False)

    def __attrs_post_init__(self):
        self.hostname = f"{self.instance_name}.example.net"


async def publish(queue, asset_connection):
    # TODO: Subscribe to drone kit server and publish messages from there
    def handle_change(attr_name, msg):
        logging.info("%s : %s", attr_name, msg)
        payload = handlers[attr_name](msg) if handlers[attr_name] else msg
        data = {"name": attr_name, "data": payload}
        print(data)
        # TODO: Add data to the queue for consumption.
        # asyncio.create_task(queue.put(data))

    rate_limiter = RateLimiter()
    for data_point in asset_data_points:
        asset_connection.add_message_listener(
            data_point,
            lambda _self, name, value: rate_limiter.run(handle_change, name, value),
        )
    choices = string.ascii_lowercase + string.digits
    # while True:
    #     msg_id = str(uuid.uuid4())
    #     host_id = "".join(random.choices(choices, k=4))
    #     instance_name = f"cattle-{host_id}"
    #     msg = PubSubMessage(message_id=msg_id, instance_name=instance)
    #     asyncio.create_task(queue.put(msg))
    #     logging.debug(f"Published message {msg}")
    #     await asyncio.sleep(random.random())


async def save(msg):
    await asyncio.sleep(random.random())
    # TODO: Send message to server over mqtt.
    # if random.randrange(1, 5) == 3:
    #     raise Exception(f"Could not save {msg}")
    logging.info(f"Saved {msg} into database")


async def cleanup(msg, event):
    await event.wait()
    await asyncio.sleep(random.random())
    msg.acked = True
    logging.info(f"Done. Acked {msg}")


def handle_results(results, msg):
    for result in results:
        if isinstance(result, Exception):
            logging.error(f"Handling general error: {result}")


async def handle_message(msg):
    event = asyncio.Event()

    asyncio.create_task(cleanup(msg, event))

    results = await asyncio.gather(save(msg), return_exceptions=True)
    handle_results(results, msg)
    event.set()
    msg.task_done()


async def consume(queue, asset_connection):
    while True:
        msg = await queue.get()
        logging.info(f"Pulled {msg}")
        asyncio.create_task(handle_message(msg))


def handle_exception(loop, context, asset_connection):
    msg = context.get("exception", context["message"])
    logging.error(f"Caught exception: {msg}")
    logging.info("Shutting down...")
    asyncio.create_task(shutdown(loop, asset_connection))


async def shutdown(loop, asset_connection, signal=None):
    if signal:
        logging.info(f"Received exit signal {signal.name}...")

    logging.info("Nacking outstanding messages")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    logging.info("Closing mqtt connection")
    client.disconnect()

    logging.info("Closing asset connection")
    asset_connection.close()

    [task.cancel() for task in tasks]
    logging.info("Cancelling outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    logging.info(f"Flushing metrics")
    loop.stop()


async def connect_to_client():
    async def connect():
        def on_connect(client, userdata, flags, rc):
            logging.info("Mqtt client connected to: " + client._host)

        def on_disconnect(client, userdata, rc):
            logging.info("Disconnected from: " + client._host)

        global client
        client = mqtt.Client()
        client.username_pw_set(username, password)
        client.tls_set()
        client.loop_start()
        client.connect(host, port=8883, keepalive=16)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        return client

    await asyncio.gather(connect(), return_exceptions=True)


def service():
    logging.info(f"ENV: {env}")
    logging.info(f"Initializing {asset_host_name}-{asset_host_id}")
    loop = asyncio.get_event_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    queue = asyncio.Queue()

    try:
        """
        `connect` requires a virtual drone running on your computer
         see: https://dronekit-python.readthedocs.io/en/latest/develop/sitl_setup.html
        Production: "127.0.0.1:14550"
        """
        asset_connection = None
        try:
            asset_connection = connect(asset_tcp_endpoint, wait_ready=True)
        except:
            logging.error("Failed to initialize connection to drone, is it running?")
        if not asset_connection:
            loop.stop()
            return
        internet_access = False
        retries = 0
        logging.info(f"Checking internet connection")
        while not internet_access:
            internet_access = check_internet_connection()
            if internet_access:
                logging.info(f"Connected to the internet, proceeding")
            else:
                logging.info(
                    f"Failed to receive internet response, retrying. Retries: {retries}"
                )
            time.sleep(retries / 4)
            retries += 1
        loop.create_task(connect_to_client())
        loop.set_exception_handler(
            lambda loop, context: handle_exception(loop, context, asset_connection)
        )
        for s in signals:
            loop.add_signal_handler(
                s,
                lambda s=s: asyncio.create_task(
                    shutdown(loop, asset_connection, signal=s)
                ),
            )
        loop.create_task(publish(queue, asset_connection))
        loop.create_task(consume(queue, asset_connection))
        loop.run_forever()
    finally:
        loop.close()
        logging.info(f"Successfully shutdown {instance}.")
