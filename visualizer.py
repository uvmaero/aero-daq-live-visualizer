# from twisted.application.internet import TCPServer, task
# from twisted.application.service import Application
# from twisted.web.resource import Resource
# from twisted.web.server import Site
# from twisted.web.static import File
# import json
# import time
# import random
# import os
# import signal
# import numpy as np
# import csv

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_daq as daq
import plotly.graph_objs as go

import numpy as np

from cefpython3 import cefpython as cef
import sys
from multiprocessing import Process
import signal
import configparser
import serial
import time
from datetime import datetime

PORT = 8050
VEHICLE_NAME = ""

SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD_RATE = 115200

# Temperature bands
CONTROLLER_TEMP_HIGH = 50
CONTROLLER_TEMP_LOW = 80
MOTOR_TEMP_HIGH = 50
MOTOR_TEMP_LOW = 80
BATTERY_TEMP_HIGH = 40
BATTERY_TEMP_LOW = 60

NUM_CELLS = 72

data = []
data_iterator = 0

CELL_TEMP_STDEV = 5
CELL_VOLT_STDEV = 0.05

kill_thread = False

ser = None

time_axis = [datetime.fromtimestamp(time.time() - i) for i in np.arange(0,10,0.5)]
cell_temp_min = [0 for i in np.arange(0,10,0.5)]
cell_temp_max = [0 for i in np.arange(0,10,0.5)]
cell_temp_avg = [0 for i in np.arange(0,10,0.5)]

class Visualizer:
    def __init__(self):
        # parse the configuration
        self.parse_config()

        # data
        self.speed = 0
        self.soc = 0.7
        self.throttle = 0
        self.current = 0
        self.cell_volt = [3.6 for i in range(NUM_CELLS)]
        self.cell_temp = [20 for i in range(NUM_CELLS)]
        self.controller_temp = 20
        self.motor_temp = 20
        self.pitch = 0

        self.theme = {
            'dark': True,
            'detail': '#00EA64',
            'primary': '#00EA64', 
            'secondary': '#d1d1d1'
        }

        self.app = dash.Dash(__name__)
        self.app.layout = html.Div([
            html.Div([
                html.H1(f'Live Telemetry Data – {VEHICLE_NAME}', style={'display': 'inline-block'})
            ]),

            daq.DarkThemeProvider(theme=self.theme, children=[
                # Gauges
                html.Div([
                    daq.Gauge(
                        id = 'speed-gauge',
                        label = 'Speed',
                        min = 0,
                        max = 80,
                        value = 20,
                        showCurrentValue = True,
                        units = 'MPH',
                        color = '#00EA64',
                        style={'display': 'inline-block'}
                    ),

                    daq.Gauge(
                        id = 'throttle-gauge',
                        label = 'Throttle',
                        min = 0,
                        max = 100,
                        value = 20,
                        showCurrentValue = True,
                        units = '%',
                        color = '#00EA64',
                        style={'display': 'inline-block'}
                    ),

                    daq.Gauge(
                        id = 'current-gauge',
                        label = 'Current',
                        min = -100,
                        max = 360,
                        value = 0,
                        showCurrentValue = True,
                        units = 'Amps',
                        color = '#00EA64',
                        style={'display': 'inline-block'}
                    ),

                    daq.Gauge(
                        id = 'soc-gauge',
                        label = 'Pack Charge',
                        min = 0,
                        max = 100,
                        value = 100,
                        showCurrentValue = True,
                        units = '%',
                        color = '#00EA64',  
                        style = {'display': 'inline-block'}
                    ),

                    # Distance Remaining Display
                    daq.LEDDisplay(
                        id = 'distance-to-empty',
                        value = '15.00',
                        label = 'Distance until empty (km)',
                        style = {'vertical-align': 'top', 'display': 'inline-block', 'margin-left': 50}
                    ),

                    # Fault Indicators
                    html.Div([
                        daq.Indicator(
                            id='imd-fault',
                            label='IMD Fault',
                            color="#ff0000",
                            size=30,
                            value=True,
                            style={'margin-bottom': 20}
                        ),

                        daq.Indicator(
                            id='bms-fault',
                            label='BMS Fault',
                            color="#ff0000",
                            size=30,
                            value=False,
                            style={'margin-bottom': 20}
                        ),

                        daq.Indicator(
                            id='tms-fault',
                            label='TMS Fault',
                            color="#ff0000",
                            size=30,
                            value=False,
                            style={'margin-bottom': 20}
                        )
                    ], style = {'display': 'inline-block', 'vertical-align': 'top', 'margin-left': 50})
                ]),

                # Thermometers
                html.Div(style={'height': 350}, children=[
                    daq.Thermometer(
                        id = 'controller-temp',
                        label = 'Controller Temp',
                        min = 0,
                        max = 100,
                        value = 20,
                        showCurrentValue = True,
                        units = 'C',
                        color = '#00EA64',
                        style = {'display': 'inline-block', 'width': 150, 'height': 350, 'vertical-align': 'top'},
                        size = 230
                    ),

                    daq.Thermometer(
                        id = 'motor-temp',
                        label = 'Motor Temp',
                        min = 0,
                        max = 100,
                        value = 20,
                        showCurrentValue = True,
                        units = 'C',
                        color = '#00EA64',
                        style = {'display': 'inline-block', 'width': 150, 'height': 350, 'vertical-align': 'top'},
                        size = 230
                    ),

                    daq.Thermometer(
                        id = 'battery-temp',
                        label = 'Max. Battery Temp',
                        min = 0,
                        max = 100,
                        value = 20,
                        showCurrentValue = True,
                        units = 'C',
                        color = '#00EA64',
                        style = {'display': 'inline-block', 'width': 150, 'height': 350, 'vertical-align': 'top'},
                        size = 230
                    ),

                    dcc.Graph(
                        id = 'cell-graph',
                        style = {'display': 'inline-block'},
                        config = {'displayModeBar': False}
                    ),

                    html.Div(daq.ToggleSwitch(
                        id='val-switcher',
                        label=['Temperature', 'Voltage'],
                        value=True,
                        vertical=True
                    ), style={'display': 'inline-block', 'vertical-align': 'top', 'margin-top': 100})
                ])
            ]),

            daq.Gauge(
                id = 'pitch-gauge',
                label = 'Pitch',
                min = -0.0175,
                max = 0.0175,
                value = 20,
                showCurrentValue = True,
                units = 'radians',
                color = '#00EA64'
            ),

            # dcc.Interval(
            #     id='fast-interval',
            #     interval=100, # in milliseconds
            #     n_intervals=0
            # ),

            # dcc.Interval(
            #     id='slow-interval',
            #     interval=500, # in milliseconds
            #     n_intervals=0
            # )
        ], style={'background': '#303030', 'color': 'white'})

        # # Update all fast data
        # @self.app.callback(
        #     [Output('speed-gauge', 'value'), Output('throttle-gauge', 'value'), Output('current-gauge', 'value'), Output('pitch-gauge', 'value')],
        #     [Input('fast-interval', 'n_intervals')]
        # )
        # def update_fast_values(n):
        #     print(self.current)
        #     return self.speed, self.throttle, self.current, self.pitch

        # # Update all slow data
        # @self.app.callback(
        #     [
        #         Output('soc-gauge', 'value'),
        #         Output('controller-temp', 'value'), Output('controller-temp', 'color'),
        #         Output('motor-temp', 'value'), Output('motor-temp', 'color'),
        #         Output('battery-temp', 'value'), Output('battery-temp', 'color'),
        #     ],
        #     [
        #         Input('slow-interval', 'n_intervals')
        #     ]
        # )
        # def update_slow_values(n):
        #     battery_temp = np.max(self.cell_temp)

        #     # Determine the color for the controller thermometer
        #     if self.controller_temp > CONTROLLER_TEMP_HIGH:
        #         controller_temp_color = '#ff0000'
        #     elif self.controller_temp > CONTROLLER_TEMP_LOW:
        #         controller_temp_color = '#ffff00'
        #     else:
        #         controller_temp_color = '#00EA64'

        #     # Determine the color for the controller thermometer
        #     if self.motor_temp > MOTOR_TEMP_HIGH:
        #         motor_temp_color = '#ff0000'
        #     elif self.motor_temp > MOTOR_TEMP_LOW:
        #         motor_temp_color = '#ffff00'
        #     else:
        #         motor_temp_color = '#00EA64'

        #     # Determine the color for the controller thermometer
        #     if battery_temp > BATTERY_TEMP_HIGH:
        #         battery_temp_color = '#ff0000'
        #     elif battery_temp > BATTERY_TEMP_LOW:
        #         battery_temp_color = '#ffff00'
        #     else:
        #         battery_temp_color = '#00EA64'
            
        #     return self.soc, self.controller_temp, controller_temp_color, self.motor_temp, motor_temp_color, battery_temp, battery_temp_color

        # # Update the cell table
        # @self.app.callback(Output('cell-graph', 'figure'), [Input('slow-interval', 'n_intervals'), Input('val-switcher', 'value')])
        # def update_cell_graph( n, val):
        #     cell_number = [i for i in range(NUM_CELLS)]
        #     if val:
        #         cell_data = self.cell_volt
        #         title = 'Cell Voltages'
        #     else:
        #         cell_data = self.cell_temp
        #         title = 'Cell Temperatures'

        #     fig = {
        #         'data': [
        #             {'x': cell_number, 'y': cell_data, 'type': 'bar', 'name': 'Cell Temp'}
        #         ],
        #         'layout': {
        #             'title': title,
        #             'titlefont': {
        #                 'color': 'white'
        #             },
        #             'paper_bgcolor': '#303030',
        #             'plot_bgcolor': '#303030',
        #             'legend': {
        #                 'font': {
        #                     'color': 'white'
        #                 }
        #             },
        #             'xaxis': {
        #                 'linecolor': 'white',
        #                 'gridcolor': '#505050',
        #                 'titlefont': {
        #                     'color': 'white'
        #                 },
        #                 'tickfont': {
        #                     'color': 'white'
        #                 }
        #             },
        #             'yaxis': {
        #                 'linecolor': 'white',
        #                 'gridcolor': '#505050',
        #                 'titlefont': {
        #                     'color': 'white'
        #                 },
        #                 'tickfont': {
        #                     'color': 'white'
        #                 }
        #             },
        #             'width': 800,
        #             'height': 350,
        #             'margin': {
        #                 'l': 20,
        #                 'r': 20,
        #                 'b': 40,
        #                 't': 30,
        #                 'pad': 0
        #             }
        #         }
        #     }
            
        #     return fig

    def start(self):
        # create a thread for the GUI app
        #Thread(target = app_thread).start()
        try:
            # create a thread for the serial monitor
            app_thread = Process(target = self.dash_app)
            app_thread.start()

            self.app.run_server(port=8000, debug=False)

            # try:
            #     with serial.Serial(SERIAL_PORT, SERIAL_BAUD_RATE) as ser:
            #         data = ser.readline().decode()
            #         if data != '':
            #             fields = data.split(' ')
            #             if fields[0] == 'RX':
            #                 print('got new data')
            #                 print(fields)
            #                 if fields[1] == 'throttle':
            #                     self.throttle = float(fields[2])
            #                 elif fields[1] == 'cell_temp':
            #                     self.cell_temp[int(fields[2])] = float(fields[3])
            #                 elif fields[1] == 'cell_volt':
            #                     self.cell_volt[int(fields[2])] = float(fields[3])
            #                 elif fields[1] == 'current':
            #                     self.current = float(fields[2])
            #                     print(f'setting current to {self.current}')
            #                 elif fields[1] == 'soc':
            #                     self.soc = float(fields[2])
            #                 elif fields[1] == 'speed':
            #                     self.speed = float(fields[2])
            #                 elif fields[1] == 'pitch':
            #                     self.pitch = float(fields[2])
            #                     print(f'setting pitch to {self.pitch}')
            # except serial.serialutil.SerialException:
            #     print("No serial device found")
            #     app_thread.terminate()
            #     exit()


        except KeyboardInterrupt:
            app_thread.terminate()

    def parse_config(self):
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

    def dash_app(self):
        pass
        

if __name__ == "__main__":
    visualizer = Visualizer()
    visualizer.start()

