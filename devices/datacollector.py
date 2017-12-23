from devices.devices import *
from yoctopuce.yocto_api import *
from threading import Thread
import time

import logging
logger = logging.getLogger(__name__)

collected_data = []

class DataCollector(Thread):

    def __init__(self, timeout=2):
        super().__init__()
        self.get_collectable_devices()
        self.timeout = timeout
        pass

    def get_collectable_devices(self):
        chirps = [get_chirp_interface(config) for config in detect_chirp_devices()]
        yoctos = []
        for yocto in detect_yocto_devices():
            yoctos.extend(get_yocto_interface(yocto))
        self.devices = chirps + yoctos

    def start(self):
        logger.info("Starting DataCollector thread")
        self.stop = False
        super().start()

    def stop(self):
        logger.info("Stopping DataCollector thread")
        self.stop = True

    def run(self):
        while not self.stop:
            self.measure_all()
            time.sleep(self.timeout)

    def measure_all(self):
        logger.debug("Measuring all devices")

        chirps = [get_chirp_interface(config) for config in detect_chirp_devices()]
        yoctos = []
        for yocto in detect_yocto_devices():
            yoctos.extend(get_yocto_interface(yocto))
        devices = chirps + yoctos

        for device in devices:
            if isinstance(device, YSensor):
                self.read_from_yocto(device)
            elif device.has_attr("address"):
                # could do isinstance(device, Chirp), but then need to import Chirp,
                # which might fail on non-raspbery...
                self.read_from_chirp(device)

    def read_from_yocto(self, yocto):
        try:
            value = yocto.get_currentValue()
            serial = yocto.get_module().get_serialNumber()
            print(serial, yocto.get_functionId(), value)
            if not serial in collected_data:
                collected_data[serial] = dict()
            collected_data[serial][yocto.get_functionId()] = value
        except:
            pass

    def read_from_chirp(self, chirp):
        chirp.trigger()
        collected_data[chirp.sensor_address] = {
            "moisture" : chirp.moist,
            "moisture-percent": chirp.moist_percent,
            "temperature" : chirp.temp
        }
