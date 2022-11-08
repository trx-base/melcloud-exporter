#!/usr/bin/env python3
# encoding: utf-8

__author__ = "Oliver Schlueter"
__license__ = "GPL"
__version__ = "1.0.0"
__email__ = "oliver.schlueter@dell.com"
__status__ = "Production"

""""
###########################################################################################################
  Prometheus Exporter for Mitsubishi MelCloud Devices
  
 Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
  and associated documentation files (the "Software"), to deal in the Software without restriction, 
  including without limitation the rights to use, copy, modify, merge, publish, distribute, 
  sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is 
  furnished to do so, subject to the following conditions:
  The above copyright notice and this permission notice shall be included in all copies or substantial 
  portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT 
  LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###########################################################################################################
"""

import os
import time
import json
import requests
import datetime
from prometheus_client import start_http_server, Gauge, Info, Enum


class MelCloudMetrics:
    headers = {
        "Content-Type": "application/json",
        "Host": "app.melcloud.com",
        "Cache-Control": "no-cache"
    }

    def __init__(self, polling_interval_seconds, mel_cloud_user, mel_cloud_password):
        self.polling_interval_seconds = polling_interval_seconds
        self.mel_cloud_user = mel_cloud_user
        self.mel_cloud_password = mel_cloud_password

        self.data = {
            "Email": self.mel_cloud_user,
            "Password": self.mel_cloud_password,
            "AppVersion": "1.23.4.0"
        }
        # Prometheus' metrics to collect
        self.device_name = Info("device_name", "Device Name")
        self.power = Enum('power_state', 'Power Status', ['room'], states=['on', 'off'])
        self.total_energy_consumed = Gauge("total_energy_consumed", "Total Energy Consumed", ['room'])
        self.wifi_signal = Gauge("wifi_signal", "Wifi Signal", ['room'])
        self.room_temperature = Gauge("room_temperature", "Room Temperature", ['room'])
        self.target_temperature = Gauge("target_temperature", "Target Temperature", ['room'])
        self.operation_mode = Enum('operation_mode', 'Operation Mode', ['room'],
                                   states=["heat", "dry", "cool", "fan_only", "heat_cool", "undefined"])
        self.fan_speed = Gauge('fan_speed', 'Fan Speed', ['room'])
        self.vane_horizontal = Gauge('vane_horizontal', 'Vane Horizontal', ['room'])
        self.vane_vertical = Gauge('vane_vertical', 'Vane Vertical', ['room'])

    def retrieve_mel_cloud_data(self):
        timestamp = datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S)")
        try:
            # try to get token
            url = 'https://app.melcloud.com/Mitsubishi.Wifi.Client/Login/ClientLogin'
            response = requests.post(url, headers=self.headers, data=json.dumps(self.data))
            out = json.loads(response.text)
            token = out['LoginData']['ContextKey']
            self.headers["X-MitsContextKey"] = token
        except Exception as err:
            print(timestamp + ": Not able to get token: " + str(err))

        try:
            # try to get device data
            url = 'https://app.melcloud.com/Mitsubishi.Wifi.Client/User/Listdevices'
            response = requests.get(url, headers=self.headers, data=json.dumps(self.data))
            out = json.loads(response.text)
            devices = out[0]['Structure']['Devices']
        except Exception as err:
            print(timestamp + ": Not able to get device data: " + str(err))

        for device in devices:
            room = device['DeviceName']

            self.device_name.info({"device_name": room})

            print(device['Device']['Power'])
            if device['Device']['Power']:
                self.power.labels(room).state("on")
            else:
                self.power.labels(room).state("off")

            self.total_energy_consumed.labels(room).set(device['Device']['CurrentEnergyConsumed'])
            self.wifi_signal.labels(room).set(device['Device']['WifiSignalStrength'])

            self.room_temperature.labels(room).set(device['Device']['RoomTemperature'])
            self.target_temperature.labels(room).set(device['Device']['SetTemperature'])

            # 1: Heating, 2: Drying, 3: Cooling, 7: Van, 8: Auto
            if device['Device']['OperationMode'] == 1:
                self.operation_mode.labels(room).state("heat")
            if device['Device']['OperationMode'] == 2:
                self.operation_mode.labels(room).state("dry")
            if device['Device']['OperationMode'] == 3:
                self.operation_mode.labels(room).state("cool")
            if device['Device']['OperationMode'] == 7:
                self.operation_mode.labels(room).state("fan_only")
            if device['Device']['OperationMode'] == 8:
                self.operation_mode.labels(room).state("heat_cool")

            self.fan_speed.labels(room).set(device['Device']['FanSpeed'])
            self.vane_horizontal.labels(room).set(device['Device']['VaneVerticalDirection'])
            self.vane_vertical.labels(room).set(device['Device']['VaneHorizontalSwing'])

    def run_metrics_loop(self):
        while True:
            self.retrieve_mel_cloud_data()
            time.sleep(self.polling_interval_seconds)


def main():
    """Main entry point"""
    try:
        polling_interval_seconds = int(os.environ['MEL_CLOUD_PORT_INTERVAL'])
    except:
        polling_interval_seconds = 10

    try:
        port = int(os.environ['MEL_CLOUD_PORT'])
    except:
        port = 8020

    try:
        mel_cloud_user = os.environ['MEL_CLOUD_USER']
    except:
        mel_cloud_user = "user"

    try:
        mel_cloud_password = os.environ['MEL_CLOUD_PASSWORD']
    except:
        mel_cloud_password = "password!"

    app_metrics = MelCloudMetrics(polling_interval_seconds, mel_cloud_user, mel_cloud_password)
    start_http_server(port)
    app_metrics.run_metrics_loop()

    
if __name__ == "__main__":
    main()
