from yoctopuce.yocto_api import *
from yoctopuce.yocto_relay import *
from threading import Thread
import configparser

import logging
logger = logging.getLogger(__name__)

class yocto_ctx(object):
    def __enter__(self):
        _init_yocto_api()

    def __exit__(self, type, value, traceback):
        pass
        # try:
        #     YAPI.FreeAPI()
        # except:
        #     pass

def _init_yocto_api():
    errmsg = YRefParam()
    # Setup the API to use local USB devices
    if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
        logger.error("Yocto init error" + str(errmsg))
        return False

    return True

def get_chirp_interface(chirp_config):
    from lib.chirp.chirp import Chirp
    return Chirp(
            address=chirp_config["address"],
            read_moist=True,
            read_temp=True,
            read_light=False,
            min_moist=chirp_config.get("calibration-min", 240),
            max_moist=chirp_config.get("calibration-max", 750),
            temp_scale='celsius',
            temp_offset=0
            )

def detect_chirp_devices():
    chirp_addresses = detect_i2c_devices()
    config = configparser.ConfigParser()
    config.read('config.ini')
    chirps = []
    for chirp_address in chirp_addresses:
        hex_addr = str(hex(chirp_address))
        if hex_addr in config and config[hex_addr]['type'] == "chirp":
            chirps.append({
                "address" : hex_addr,
                "name" : config[hex_addr]['logical-name'],
                "calibration-min" : int(config[hex_addr]['calibration-min']),
                "calibration-max" : int(config[hex_addr]['calibration-max'])
            })
        else:
            chirps.append({
                "address" : hex_addr,
                "name" : "",
                "calibration-min" : 240,
                "calibration-max" : 750
            })
    return chirps

def detect_i2c_devices():
    """ returns the addresses where I2C devices are responding """
    try:
        import smbus
        bus = smbus.SMBus(1) # 1 indicates /dev/i2c-1
        addresses = []
        for device in range(128):
              try:
                 bus.read_byte(device)
                 addresses.append(hex(device))
              except: # exception if read_byte fails
                 pass
        return addresses
    except ModuleNotFoundError:
        logger.error("Couldn't load smbus module. Cannot identify I2C devices.")
        return []

def chirp_rename_device(address, newname):
    config = configparser.ConfigParser()
    config.read('config.ini')
    if address not in config:
        return "There is no device with address "

    config[address]["logical-name"] = newname
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    return None

def chirp_calibrate_device(address, minimum, maximum):
    config = configparser.ConfigParser()
    config.read('config.ini')
    if address not in config:
        return "There is no device with address "

    config[address]["calibration-min"] = minimum
    config[address]["calibration-max"] = maximum
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    return None

def detect_yocto_devices():
    with yocto_ctx():

        config = configparser.ConfigParser()
        config.read('config.ini')

        modules = []
        module = YModule.FirstModule()
        while module is not None:
            desc = {
                "serial" : module.get_serialNumber(),
                "type" : module.get_productName(),
                "logical-name" : module.get_logicalName(),
                "functions" : []
            }
            for i in range(module.functionCount()):
                datacollection = False
                if module.get_serialNumber() in config and module.functionId(i) in config[module.get_serialNumber()]:
                    datacollection = config[module.get_serialNumber()][module.functionId(i)].upper() == "TRUE"

                sensor_id = "{}.{}".format(desc["serial"], module.functionId(i))
                func = YSensor.FindFunction(sensor_id)
                if func.isOnline():
                    desc["functions"].append({
                        "funcId" : module.functionId(i),
                        "logical-name" : module.functionName(i),
                        "data-collection" : datacollection,
                        "value" : module.functionValue(i)
                    })
            modules.append(desc)
            module = module.nextModule()

    return modules

def get_yocto_interface(config):
    with yocto_ctx():
        serial = config["serial"]
        sensors = []
        for func in config["functions"]:
            funcId = func["funcId"]
            identifier = "{}.{}".format(serial, funcId)
            sensor = YSensor.FindSensor(identifier)
            sensors.append(sensor)
        return sensors

def yocto_identify_device(identifier):
    def blink_module(module):
        print("start")
        with yocto_ctx():
            module.set_beacon(YModule.BEACON_ON)
        print("sleep")
        time.sleep(10)
        print("stop")
        with yocto_ctx():
            module.set_beacon(YModule.BEACON_OFF)
        logger.debug("Stopped blinking. Bye.")

    online = False
    with yocto_ctx():
        module = YModule.FindModule(identifier)
        online = module.isOnline()

    if online:
        logger.info("Found %s - blinking for 10 seconds", identifier)
        t = Thread(target=blink_module, args=[module])
        t.start()
    else:
        logger.warn("Couldn't find device %s", identifier)
        return "Couldn't identify device %s because I couldn't find it" % identifier

    return None

def yocto_set_logical_name(identifier, new_name):
    with yocto_ctx():
        module = YModule.FindModule(identifier)
        if not module.isOnline():
            logger.error("Couldn't find device %s", identifier)
            return "Couldn't set name for device %s because I couldn't find it" % identifier
        else:
            logger.debug("Changing device name of module %s (serial %s) to %s", module.get_logicalName(), module.get_serialNumber(), new_name)
            module.set_logicalName(new_name)
            module.saveToFlash()
            return None

def yocto_set_logical_name_sensor(module, sensor, new_name):
    with yocto_ctx():
        identifier = "{}.{}".format(module, sensor)
        sensor = YSensor.FindFunction(identifier)
        if not sensor.isOnline():
            logger.error("Couldn't find device %s", identifier)
            return "Couldn't set name for sensor %s because I couldn't find it" % identifier
        else:
            logger.debug("Changing device name of sensor %s (%s) to %s", module, identifier, new_name)
            sensor.set_logicalName(new_name)
            sensor.get_module().saveToFlash()
            return None

def yocto_set_data_collection(module, sensor, on_off):
    config = configparser.ConfigParser()
    config.read('config.ini')

    if not module in config:
        config[module] = {}
    config[module][sensor] = str(on_off == "ON")
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    return None


def activate_relay_seconds(module, function, duration):
    def activate(relay, duration):
        with yocto_ctx():
            relay.set_state(YRelay.OUTPUT_ON)
        time.sleep(duration)
        with yocto_ctx():
            relay.set_state(YRelay.OUTPUT_OFF)
        logger.debug("Stopped relay %s. Bye.")

    with yocto_ctx():
        identifier = "{}.{}".format(module, function)
        relay = YRelay.FindRelay(identifier)
        if relay.isOnline():
            logger.info("Found %s - activating for %s seconds", identifier, duration)
            t = Thread(target=activate, args=[relay, duration])
            t.start()
            return "Activated relay %s for %s seconds" % (identifier, duration)
        else:
            logger.warn("Couldn't find relay %s", identifier)
            return "Couldn't identify device %s because I couldn't find it" % identifier

def toggle_relay(module, function):
    with yocto_ctx():
        identifier = "{}.{}".format(module, function)
        relay = YRelay.FindRelay(identifier)
        if relay.isOnline():
            logger.info("Found %s - toggling", identifier)
            if relay.get_state() == YRelay.OUTPUT_OFF:
                relay.set_state(YRelay.OUTPUT_ON)
            else:
                relay.set_state(YRelay.OUTPUT_OFF)
            return "Toggled %s" % identifier
        else:
            logger.warn("Couldn't find relay %s", identifier)
            return "Couldn't identify device %s because I couldn't find it" % identifier
