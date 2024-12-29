import logging
import paho.mqtt.client as mqtt_client
from getmac import get_mac_address

logger = logging.getLogger(__name__)


class MqttClient(object):
    def __init__(self, mqtt_host, mqtt_port):
        logger.debug("MQTT init")
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.client_id = get_mac_address().replace(':', '') + "-mqtt"
        self.client = mqtt_client.Client(client_id=self.client_id)

    def connect(self):
        logger.debug("Connection to %s:%s with client id: %s", self.mqtt_host, self.mqtt_port, self.client_id)
        self.client.loop_start()
        self.client.connect(self.mqtt_host, self.mqtt_port)

    def subscribe(self):
        def on_message(client, userdata, msg):
            logger.debug(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            # TODO: insert from year the AI management

        self.client.on_message = on_message
        self.client.subscribe(get_mac_address())
        
    def publish(self, topic, message):
        self.client.publish(topic, message)

    def disconnect(self):
        logger.debug("Disconnection")
        self.client.loop_stop()
        self.client.disconnect()
