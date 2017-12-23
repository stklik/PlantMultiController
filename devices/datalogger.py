import configparser
import time
import socket
from threading import Thread
from devices.devices import *
from Adafruit_IO import Client, MQTTClient

class DataLogger(Thread):

    def setup_ada_client(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.client = Client(config["adafruit"]["adafruit-io-key"])

    def start(self):
        logger.info("Starting DataLogger thread")
        self.setup_ada_client()
        self.stop = False
        super().start()

    def stop(self):
        logger.info("Stopping DataLogger thread")
        self.stop = True

    def run(self):
        while not self.stop:
            self.log_all()
            config = configparser.ConfigParser()
            config.read('config.ini')
            timeout = 10
            if "logging" in config and "timeout" in config["logging"]:
                timeout = config["logging"]["timeout"]
            time.sleep(int(timeout))

    def log_all(self):
        yoctos = detect_yocto_devices()
        for yocto in yoctos:
            for function in yocto["functions"]:
                if function["data-collection"]:
                    host = socket.gethostname()
                    device = yocto["logical-name"] if yocto["logical-name"].strip() else yocto["serial"]
                    func = function["logical-name"] if function["logical-name"].strip() else function["serial"]

                    feed = "---".join([host, device, func])
                    value = function["value"]
                    self.log(feed, value)

    def log(self, feed, value):
        feed = feed.replace(".", "-")
        try:
            self.client.send(feed, value)
        except:
            logging.error("Error when sending value %s (type: %s) to feed %s", value, type(value), feed, exc_info=True)
