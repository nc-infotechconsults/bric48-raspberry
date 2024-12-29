import argparse
import logging
import time

from ble.controller import BleController
from backend.mqtt import MqttClient
from backend.rest import RestClient

# configure logging
logging.basicConfig(level=logging.DEBUG,
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
        # Creating objects
        mqtt_client = MqttClient(args.mqtt_host, args.mqtt_port)
        rest_client = RestClient(args.backend_base_url)
        ble_controller = BleController()
        
        # obtain user info 
        user_info = rest_client.get_user_info()
        user_language = user_info['language']   # used to reproduce the correct voice
        
        # obtain machineries map
        machineries = rest_client.get_all_machineries()
        print(machineries)
        
        # connect mqtt
        mqtt_client.connect()
        
        # subscribe to topic 
        mqtt_client.subscribe()
        
        try:
            ble_controller.scan()
        except KeyboardInterrupt:
            mqtt_client.disconnect()
            
    except Exception as e:
        print(e)
        mqtt_client.disconnect()
        exit(-1)

    logger.info("Application exit with status code 0")
    exit(0)

main()
