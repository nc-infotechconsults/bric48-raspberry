import logging

from bleak import BleakScanner

logger = logging.getLogger(__name__)

class BleController(object):
    def __init__(self, machineries, mqtt_client):
        
        self.beacons_machinery = {}
        self.beacon_serials = []
        self.beacons_threshold = {}
        
        for machinery in machineries:
            for beacon in machinery['beacons']:
                self.beacon_serials.append(beacon['serial'])
                self.beacons_machinery[beacon['serial']] = machinery['id']
                self.beacons_threshold[beacon['serial']] = beacon['threshold']
        
        self.machineries = machineries
        self.mqtt_client = mqtt_client

    async def scan(self):
        async with BleakScanner() as scanner:
            await scanner.discover(timeout=1, return_adv=True)
            for addr, dev_adv in scanner.discovered_devices_and_advertisement_data.items():
                logger.info("Device: %s, RSSI: %s", addr, dev_adv[1].rssi)
                
                if addr in self.beacon_serials:
                    if dev_adv[1].rssi > -self.beacons_threshold[addr]:
                        self.mqtt_client.user_near_machinery(self.beacons_machinery[addr])
                    else:
                        self.mqtt_client.user_far_machinery(self.beacons_machinery[addr])
                
                
                