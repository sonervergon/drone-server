# Drone service

> Runs on the drone and creates a connection between the drone software and the core service.

## Prerequisites

1. Everything is ran with `python3`, make sure you have the right version.
2. Install paho mqtt client: [reference](https://www.eclipse.org/paho/index.php?page=clients/python/index.php).
3. Install `dronekit`: [reference](https://dronekit-python.readthedocs.io/en/latest/guide/quick_start.html).
4. Install `python-dotenv`: [reference](https://pypi.org/project/python-dotenv/).
5. Install `attrs` version >= `18.1.0`

## Instructions

The environment variables in the `.env` file are secret and should not be shared.

**TLDR: To start service locally**

1. Start drone, run `dronekit-sitl copter` in terminal.
2. Start drone service, run `python3 __init__.py` from root.
