from dronekit import VehicleMode, LocationGlobalRelative
import logging


def set_vehicle_mode(asset_connection, mode):
    asset_connection.mode = VehicleMode(mode)


def arm_vehicle(asset_connection):
    asset_connection.arm()
    asset_connection.armed = True


handlers = {
    "ARM": lambda asset_connection, payload: asset_connection.arm(),
    "DISARM": lambda asset_connection, payload: asset_connection.disarm(),
    "MODE": lambda asset_connection, payload: set_vehicle_mode(
        asset_connection, payload
    ),
}


def process_inbound_drone_instruction(msg, asset_connection):
    name = msg["name"]
    action = msg["payload"]["action"]
    logging.info(name + ": " + action)
    payload = msg["payload"]["payload"]
    if action in handlers:
        handlers[action](asset_connection, payload)
