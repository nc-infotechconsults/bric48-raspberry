from bluepy.btle import Scanner
from ble.delegate import ScanDelegate


class BleController(object):
    def __init__(self):
        self.scanner = Scanner().withDelegate(ScanDelegate())

    def scan(self):
        while True:
            devices = self.scanner.scan(1)
            print(devices)
