from twisted.application.internet import TCPServer, task
from twisted.application.service import Application
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File
import json
import time
import random
import os
import signal
import numpy as np
import csv
from cefpython3 import cefpython as cef
import sys
from threading import Thread
import configparser
import serial

PORT = 8000
VEHICLE_NAME = ""

SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD_RATE = 115200

speed = 0
soc = 0.7
throttle = 0
current = 0
cell_volt = [0 for i in range(0,80)]
cell_temp = [0 for i in range(0,80)]

data = []
data_iterator = 0

CELL_TEMP_STDEV = 5
CELL_VOLT_STDEV = 0.05

kill_thread = False

ser = None

def kill_twistd():
    # kill the server by pulling the pid from the pid file and sending it a SIGTERM
    # this is janky, but whatever
    with open("twistd.pid", "r") as f:
        pid = int(f.readline())
    os.kill(pid, signal.SIGTERM)

class GetDataHandler(Resource):
    def render_POST(self, request):
        # create json blob
        output_json = {
            'timestamp': int(time.time()*1000),  # timestamp in milliseconds
            'vehicle_name': VEHICLE_NAME,
            'speed': speed,
            'soc': soc,
            'throttle': throttle,
            'current': current,
            'cell_volt': cell_volt,
            'cell_temp': cell_temp
        }

        # create json string
        output_json_str = json.dumps(output_json)

        # return json string
        return bytes(output_json_str, 'utf-8')

class CloseHandler(Resource):
    def render_POST(self, resource):
        kill_twistd()

# desktop app thread
def app_thread():
    global kill_thread
    sys.excepthook = cef.ExceptHook
    cef.Initialize()
    cef.CreateBrowserSync(url="http://localhost:"+PORT, window_title="AERO DAQ Live Visualizer")
    cef.MessageLoop()
    cef.Shutdown()
    kill_thread = True
    kill_twistd()

def serial_thread():
    global throttle, cell_volt, cell_temp, current, soc, speed
    with serial.Serial(SERIAL_PORT, SERIAL_BAUD_RATE) as ser:
        while not kill_thread:
            data = ser.readline().decode()
            if data != '':
                print(data)
                fields = data.split(' ')
                print(fields)
                if fields[0] == 'RX':
                    if fields[1] == 'throttle':
                        throttle = float(fields[2])
                    elif fields[1] == 'cell_temp':
                        cell_temp[int(fields[2])] = float(fields[3])
                    elif fields[1] == 'cell_volt':
                        cell_volt[int(fields[2])] = float(fields[3])
                    elif fields[1] == 'current':
                        current = float(fields[2])
                    elif fields[1] == 'soc':
                        soc = float(fields[2])
                    elif fields[1] == 'speed':
                        speed = float(fields[2])
                


def parse_config():
    global PORT, VEHICLE_NAME, SERIAL_PORT, SERIAL_BAUD_RATE
    config = configparser.ConfigParser()
    config.read('visualizer_config.ini')

    if 'WEBSERVER' in config.sections():
        PORT = config['WEBSERVER']['port']

    if 'VEHICLE' in config.sections():
        VEHICLE_NAME = config['VEHICLE']['name']

    if 'SERIAL' in config.sections():
        SERIAL_PORT = config['SERIAL']['port']
        SERIAL_BAUD_RATE = config['SERIAL']['baud_rate']

# add the html frontend app
root = File("app")

# add an endpoint for the get_data handler
root.putChild(b"get_data", GetDataHandler())

# add endpoint to close the program
root.putChild(b"close", CloseHandler())

# start main server
application = Application("AERO Data Visualizer")
server = TCPServer(PORT, Site(root)).setServiceParent(application)

# load CSV data
with open('demo_data.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)

    data = [r for r in reader]

# parse the configuration
parse_config()

# create a thread for the GUI app
Thread(target = app_thread).start()

# create a thread for the serial monitor
Thread(target = serial_thread).start()

