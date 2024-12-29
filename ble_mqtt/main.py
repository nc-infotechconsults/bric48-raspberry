import argparse
import asyncio
import logging

from backend.mqtt import MqttClient
from backend.rest import RestClient
from ble.controller import BleController

# configure logging
logging.basicConfig(level=logging.INFO,
                    format="{asctime} - {name} -  {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

# configure argoarsee
parser = argparse.ArgumentParser()
parser.add_argument("--backend_base_url", required=True, help="Backend base url. E.g. http://localhost:8080/api")
parser.add_argument("--mqtt_host", required=True, help="MQTT Broker IP")
parser.add_argument("--topic_user_near", required=False, help="MQTT Broker Topic where to publish that user is near to a machinery", default="user-near-machinery")
parser.add_argument("--topic_user_far", required=False, help="MQTT Broker Topic where to publish that user is far from a machinery", default="user-far-machinery")
parser.add_argument("--mqtt_port", required=False, help="MQTT Broker Port. Defualt: 1883", default=1883)


def main():
    logger.info('Application started')
    args = parser.parse_args()
    logger.info('Connecting to backend: ' + args.backend_base_url)
    logger.info('Connecting to mqtt broker: %s:%s',args.mqtt_host, args.mqtt_port)
    
    try:
        # Creating rest client
        rest_client = RestClient(args.backend_base_url)
        
        # obtain user info 
        user_info = rest_client.get_user_info()
        user_language = user_info['language']   # used to reproduce the correct voice
        
        # create mqtt client
        mqtt_client = MqttClient(args.mqtt_host, args.mqtt_port, args.topic_user_near, args.topic_user_far, user_info['id'])
        
        # obtain machineries map
        machineries = rest_client.get_all_machineries()
        
        # connect mqtt
        mqtt_client.connect()
        
        # creating ble controller
        ble_controller = BleController(machineries, mqtt_client)
        
        try:
            while True:
                asyncio.run(ble_controller.scan())
        except KeyboardInterrupt:
            for machinery in machineries:
                mqtt_client.user_far_machinery(machinery['id'])
            mqtt_client.disconnect()
    except Exception as e:
        for machinery in machineries:
            mqtt_client.user_far_machinery(machinery['id'])
        mqtt_client.disconnect()
        exit(-1)

    logger.info("Application exit with status code 0")
    exit(0)

main()
