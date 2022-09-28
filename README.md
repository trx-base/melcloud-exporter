# melcloud-exporter
Python based Prometheus Exporter

Can be used as Python Code or as Docker Container. 

Creation of Docker Container:

      docker build --tag melcloud-exporter .

Starting of Docker Container with docker-compose

      docker-compose up -d

A Grafana Dashboard example is also provided as JSON template 

Credential, Ports and Polling Interval are given by environmental variables (see also the docker-compose.yml file)

      MEL_CLOUD_USER: user@domain.com
      MEL_CLOUD_PASSWORD: secret_password
      MEL_CLOUD_PORT: 8020
      MEL_CLOUD_PORT_INTERVAL: 60