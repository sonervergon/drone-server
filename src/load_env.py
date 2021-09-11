from dotenv import load_dotenv

load_dotenv("./.env")

import os


environment = {
    "env": os.environ.get("ENV"),
    "username": os.environ.get("MQTT_USERNAME"),
    "password": os.environ.get("MQTT_PASSWORD"),
    "host": os.environ.get("MQTT_HOST"),
    "port": int(os.environ.get("MQTT_PORT")),
    "asset_tcp_endpoint": os.environ.get("ASSET_TCP_ENDPOINT"),
    "asset_data": os.environ.get("ASSET_DATA"),
    "asset_host_name": os.environ.get("ASSET_HOST_NAME"),
    "asset_host_id": os.environ.get("ASSET_HOST_ID"),
    "asset_type": os.environ.get("ASSET_TYPE"),
    "asset_workspace": os.environ.get("ASSET_WORKSPACE"),
    "asset_schema_reference": os.environ.get("ASSET_SCHEMA_REFERENCE"),
}


def get(key):
    return environment[key]
