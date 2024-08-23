#!/usr/bin/env python3
# encoding: utf-8

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
from prometheus_client import start_http_server, Gauge

class MelCloudMetrics:
    headers = {
        "Content-Type": "application/json",
        "Host": "app.melcloud.com",
        "Cache-Control": "no-cache"
    }

    def __init__(self, polling_interval_seconds, mel_cloud_user, mel_cloud_password, metric_prefix):
        self.polling_interval_seconds = polling_interval_seconds
        self.mel_cloud_user = mel_cloud_user
        self.mel_cloud_password = mel_cloud_password
        self.metric_prefix = metric_prefix

        self.data = {
            "Email": self.mel_cloud_user,
            "Password": self.mel_cloud_password,
            "AppVersion": "1.23.4.0"
        }
        self.metrics = {}

    def create_or_get_metric(self, name, description, room):
        if name not in self.metrics:
            self.metrics[name] = Gauge(self.metric_prefix + "_" + name, description, ['room'])

        return self.metrics[name].labels(room)

    def retrieve_mel_cloud_data(self):
        global devices
        error = False
        timestamp = datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S)")
        try:
            url = 'https://app.melcloud.com/Mitsubishi.Wifi.Client/Login/ClientLogin'
            response = requests.post(url, headers=self.headers, data=json.dumps(self.data))
            out = json.loads(response.text)
            if out['LoginStatus'] != 0:
                print("Login not successful")
                error = True
            else:
                token = out['LoginData']['ContextKey']
                self.headers["X-MitsContextKey"] = token
        except Exception as err:
            print(timestamp + ": Not able to get token: " + str(err))
            error = True

        if not error:
            try:
                url = 'https://app.melcloud.com/Mitsubishi.Wifi.Client/User/Listdevices'
                response = requests.get(url, headers=self.headers, data=json.dumps(self.data))
                out = json.loads(response.text)
                devices = out[0]['Structure']['Devices']
                print("Retrieved devices: " + str(len(devices)) )
            except Exception as err:
                print(timestamp + ": Not able to get device data: " + str(err))
                error = True

            if not error:
                try:
                    for device in devices:
                        room = device['DeviceName']
                        for key, value in device['Device'].items():
                           if isinstance(value, (int, float, bool)):
                                metric = self.create_or_get_metric(key, key, room)
                                metric.set(float(value))

                except Exception as err:
                    print(timestamp + ": Not able to read values: " + str(err))
                    error = True

    def run_metrics_loop(self):
        while True:
            print("Polling MELCloud API with interval of " + str(self.polling_interval_seconds) + " seconds.")
            self.retrieve_mel_cloud_data()
            time.sleep(self.polling_interval_seconds)

def main():
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

    try:
        metric_prefix = os.environ['METRIC_PREFIX']
    except:
        metric_prefix = "MC"

    app_metrics = MelCloudMetrics(polling_interval_seconds, mel_cloud_user, mel_cloud_password, metric_prefix)
    start_http_server(port)
    app_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()