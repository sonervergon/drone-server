#!/usr/bin/env python3.7
"""
Based on implementation here: https://roguelynn.com/words/asyncio-testing/
to achieve concurrency and Exception tolerance.
"""


# Feature dependencies
from dronekit import connect
import paho.mqtt.client as mqtt
from load_env import get

# Service dependencies
import asyncio
import logging
import random
import signal
import string
import attr  # attrs

username = get("username")
password = get("password")
host = get("host")
port = get("port")
env = get("env")
asset_host_name = get("asset_host_name")
asset_host_id = get("asset_host_id")
asset_tcp_endpoint = get("asset_tcp_endpoint")

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s.%(msecs)d, {asset_host_id} %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


@attr.s
class PubSubMessage:
    instance_name = attr.ib()
    message_id = attr.ib(repr=False)
    hostname = attr.ib(repr=False, init=False)
    restarted = attr.ib(repr=False, default=False)
    saved = attr.ib(repr=False, default=False)
    acked = attr.ib(repr=False, default=False)
    extended_cnt = attr.ib(repr=False, default=0)

    def __attrs_post_init__(self):
        self.hostname = f"{self.instance_name}.example.net"


async def publish(queue, asset_connection):
    # TODO: Subscribe to drone kit server and publish messages from there
    choices = string.ascii_lowercase + string.digits
    # while True:
    #     msg_id = str(uuid.uuid4())
    #     host_id = "".join(random.choices(choices, k=4))
    #     instance_name = f"cattle-{host_id}"
    #     msg = PubSubMessage(message_id=msg_id, instance_name=instance_name)
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


async def extend(msg, event):
    while not event.is_set():
        msg.extended_cnt += 1
        logging.info(f"Extended deadline by 3 seconds for {msg}")
        await asyncio.sleep(2)


def handle_results(results, msg):
    for result in results:
        if isinstance(result, Exception):
            logging.error(f"Handling general error: {result}")


async def handle_message(msg):
    event = asyncio.Event()

    asyncio.create_task(extend(msg, event))
    asyncio.create_task(cleanup(msg, event))

    results = await asyncio.gather(save(msg), return_exceptions=True)
    handle_results(results, msg)
    event.set()


async def consume(queue, asset_connection):
    while True:
        msg = await queue.get()
        logging.info(f"Pulled {msg}")
        asyncio.create_task(handle_message(msg))


def handle_exception(loop, context):
    msg = context.get("exception", context["message"])
    logging.error(f"Caught exception: {msg}")
    logging.info("Shutting down...")
    asyncio.create_task(shutdown(loop))


async def shutdown(loop, signal=None):
    if signal:
        logging.info(f"Received exit signal {signal.name}...")

    logging.info("Nacking outstanding messages")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    logging.info("Closing mqtt connection")
    client.disconnect()

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
        asset = None
        try:
            asset = connect(asset_tcp_endpoint, wait_ready=True)
        except:
            logging.error("Failed to initialize connection to drone, is it on?")
        if not asset:
            loop.stop()
            return
        loop.create_task(connect_to_client())
        loop.set_exception_handler(
            lambda loop, context: handle_exception(loop, context)
        )
        for s in signals:
            loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(shutdown(loop, signal=s))
            )
        loop.create_task(publish(queue, asset))
        loop.create_task(consume(queue, asset))
        loop.run_forever()
    finally:
        loop.close()
        logging.info(f"Successfully shutdown {asset_host_name}-{asset_host_id}.")
