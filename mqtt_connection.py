import paho.mqtt.client as mqtt
from logger import init

logger = init()


def create_connection(username, password, url):
    def on_connect(client, userdata, flags, rc):
        logger.debug('Connected')

    def on_disconnect(client, userdata, rc):
        logger.debug('Disconnected')
        client.loop_stop()

    client = mqtt.Client()
    client.username_pw_set(username, password)
    client.tls_set()

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    client.loop_start()
    logger.debug('Connecting to ' + url)
    client.connect(url, port=8883, keepalive=15)
    return client

