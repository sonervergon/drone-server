handlers = {
    "ARM": lambda asset_connection: asset_connection.arm(),
    "DISARM": lambda asset_connection: asset_connection.disarm(),
}


def process_inbound_drone_instruction(msg, asset_connection):
    action = msg["payload"]["action"]
    if action in handlers:
        handlers[action](asset_connection)
