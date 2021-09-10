import paho.mqtt.client as mqtt

async def create_connection(username, password, url):

    client = mqtt.Client()
    client.username_pw_set(username, password)
    client.tls_set()

    client.loop_start()
    client.connect(url, port=8883)
    return client

