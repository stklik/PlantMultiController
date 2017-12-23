import configparser
import time
import socket
import os
from threading import Thread
from devices.devices import *
from Adafruit_IO import Client, MQTTClient

class DataLogger(Thread):

    def setup_ada_client(self):
        adafruit_key = os.getenv("ADAKEY", None)
        if not adafruit_key:
            config = configparser.ConfigParser()
            config.read('config.ini')
            adafruit_key = config["adafruit"]["adafruit-io-key"]

        self.client = Client(adafruit_key)

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
            timeout = 30
            if "logging" in config and "timeout" in config["logging"]:
                timeout = config["logging"]["timeout"]
            time.sleep(int(timeout))

    def log_all(self):
        print("Logging")
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

        chirps = detect_chirp_devices()
        for chirp in chirps:
            for function in chirp["functions"]:
                if function["data-collection"]:
                    host = socket.gethostname()
                    device = chirp["name"] if chirp["name"].strip() else chirp["address"]
                    func = function["logical-name"] if function["logical-name"].strip() else function["funcId"]

                    feed = "--".join([host, device, func])
                    value = function["value"]
                    self.log(feed, value)

    def log(self, feed, value):
        feed = feed.replace(".", "-")
        try:
            print("Log ", feed, value)
            if value != None:
                self.client.send(feed, value)
        except:
            logging.error("Error when sending value %s (type: %s) to feed %s", value, type(value), feed, exc_info=True)
