import sys
from webserver.server import app
from devices.datacollector import DataCollector
from devices.datalogger import DataLogger

import logging
collectorLog = logging.getLogger(name="devices.datacollector") # specific logging level
collectorLog.setLevel(logging.INFO)

# run the thread that reads all data
# datacollector = DataCollector()
# datacollector.start()

datalogger = DataLogger()
datalogger.start()


# start server
app.portnumber = 8080
app.run(host='0.0.0.0', port=8080)
