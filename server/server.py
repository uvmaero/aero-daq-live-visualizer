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

PORT = 8000
VEHICLE_NAME = "CleanSpeed 4.0"

speed = 0
soc = 0.7
throttle = 0
current = 0
cell_volt = [0 for i in range(0,80)]
cell_temp = [0 for i in range(0,80)]

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
        # kill the server by pulling the pid from the pid file and sending it a SIGTERM
        # this is janky, but whatever
        with open("twistd.pid", "r") as f:
            pid = int(f.readline())
        os.kill(pid, signal.SIGTERM)

def loop():
    global throttle, cell_volt, cell_temp, current, soc

    # generate fake throttle data
    throttle += 0.01
    if throttle > 1:
        throttle = 0

    # generate fake current data
    current += 5
    if current > 360:
        current = 0

    soc -= 0.0001
    if soc < 0:
        soc = 1

    # generate fake cell voltage and current data
    for i in range(0, 80):
        cell_volt[i] = random.randrange(3500, 3700)/1000
        cell_temp[i] = random.randrange(220, 250)/10
    cell_temp[7] += 35

# add the html frontend app
root = File("../dashboard")

# add an endpoint for the get_data handler
root.putChild(b"get_data", GetDataHandler())

# add endpoint to close the program
root.putChild(b"close", CloseHandler())

# start main server
application = Application("AERO Data Visualizer")
server = TCPServer(PORT, Site(root)).setServiceParent(application)

# start looping task
lc = task.LoopingCall(loop)
lc.start(0.1, now=False)