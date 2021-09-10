import asyncio
import logging
import time

restart_tries = 0

async def shutdown(loop):
    logging.info("Closing database connections")
    logging.info("Nacking outstanding messages")
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]

    [task.cancel() for task in tasks]

    logging.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    logging.info(f"Flushing metrics")
    loop.stop()

async def consume(queue):
    while True:
        msg = await queue.get()
        if random.randrange(1, 5) == 3:
            raise Exception(f"Could not consume {msg}")
        logging.info(f"Consumed {msg}")
        asyncio.create_task(handle_message(msg))

async def handle_message(msg):
    event = asyncio.Event()
    asyncio.create_task(extend(msg, event))
    asyncio.create_task(cleanup(msg, event))

    await asyncio.gather(save(msg), restart_host(msg))
    event.set()

def exception_handler(loop, context): 
    # context["message"] will always be there; but context["exception"] may not
    msg = context.get("exception", context["message"])
    logging.error(f" Caught exception: {msg}")
    logging.info("Shutting down...")
    asyncio.create_task(shutdown(loop))


def loop(serve, restart=False): 
    event_loop = asyncio.get_event_loop()
    try:
        restart_tries = 0
        # May want to catch other signals too
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(shutdown(loop, signal=s)))
        queue = asyncio.Queue()
        event_loop.create_task(serve(queue))
        event_loop.run_forever()
        event_loop.set_exception_handler(exception_handler)
    except Exception as e:
        logging.error("Event loop crashed")
        logging.error(e)
        event_loop.close()



async def serve(): 
    await asyncio.sleep(1)
    raise Exception("Server exited")

if __name__ == "__main__":
    loop(serve(), True)