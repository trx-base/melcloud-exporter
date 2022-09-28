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

import asyncio
import os
import time
import aiohttp
import pymelcloud
from prometheus_client import start_http_server, Gauge, Info, Enum


class MelCloudMetrics:

    def __init__(self, polling_interval_seconds, mel_cloud_user, mel_cloud_password):
        self.polling_interval_seconds = polling_interval_seconds
        self.mel_cloud_user = mel_cloud_user
        self.mel_cloud_password = mel_cloud_password

        # Prometheus' metrics to collect
        self.device_name = Info("device_name", "Device Name")
        self.power = Enum('power_state', 'Power Status', states=['on', 'off'])
        self.total_energy_consumed = Gauge("total_energy_consumed", "Total Energy Consumed")
        self.wifi_signal = Gauge("wifi_signal", "Wifi Signal")
        self.room_temperature = Gauge("room_temperature", "Room Temperature")
        self.target_temperature = Gauge("target_temperature", "Target Temperature")
        self.operation_mode = Enum('operation_mode', 'Operation Mode',
                                   states=["heat", "dry", "cool", "fan_only", "heat_cool", "undefined"])
        self.fan_speed = Enum('fan_speed', 'Fan Speed', states=["1", "2", "3", "4", "5", "auto"])
        self.vane_horizontal = Enum('vane_horizontal', 'Vane Horizontal', states=["1", "2", "3", "4", "5", "auto"])
        self.vane_vertical = Enum('vane_vertical', 'Vane Vertical', states=["1", "2", "3", "4", "5", "auto"])

    async def retrieve_mel_cloud_data(self):
        async with aiohttp.ClientSession() as session:
            # call the login method with the session
            token = await pymelcloud.login(self.mel_cloud_user, self.mel_cloud_password, session=session)

            # lookup the device
            devices = await pymelcloud.get_devices(token, session=session)
            device = devices[pymelcloud.DEVICE_TYPE_ATA][0]

            # perform logic on the device
            await device.update()

            self.device_name.info({"device_name": device.name})
            if device.power:
                self.power.state("on")
            else:
                self.power.state("off")

            # noinspection PyUnresolvedReferences
            self.total_energy_consumed.set(device.total_energy_consumed)
            self.wifi_signal.set(device.wifi_signal)
            # noinspection PyUnresolvedReferences
            self.room_temperature.set(device.room_temperature)
            # noinspection PyUnresolvedReferences
            self.target_temperature.set(device.target_temperature)
            # noinspection PyUnresolvedReferences
            self.operation_mode.state(device.operation_mode)
            # noinspection PyUnresolvedReferences
            self.fan_speed.state(device.fan_speed)
            # noinspection PyUnresolvedReferences
            self.vane_horizontal.state(device.vane_horizontal)
            # noinspection PyUnresolvedReferences
            self.vane_vertical.state(device.vane_vertical)

            # print(device.name)
            # print(device.units)
            # print(device.temp_unit)
            # print(device.last_seen)
            # print(device.power)
            # print(device.total_energy_consumed)
            # print(device.wifi_signal)
            # print(device.room_temperature)
            # print(device.target_temperature)
            # print(device.operation_mode)
            # print(device.fan_speed)
            # print(device.vane_horizontal)
            # print(device.vane_vertical)
            await session.close()

    def run_metrics_loop(self):
        while True:
            self.fetch()
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.retrieve_mel_cloud_data())


def main():
    """Main entry point"""
    try:
        polling_interval_seconds = int(os.environ['MEL_CLOUD_PORT_INTERVAL'])
    except:
        polling_interval_seconds = 120

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
        mel_cloud_password = "password"

    app_metrics = MelCloudMetrics(polling_interval_seconds, mel_cloud_user, mel_cloud_password )
    start_http_server(port)
    app_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()
