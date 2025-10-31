# RuuviTag

Data from RuuviTag sensor is gathered using telegraf together with the `ruuvitag_datacollector.py` script.
In addition, an influxdb instance must be set up, and an MQTT broker must be running.
See the Mosquitto MQTT broker below for information about how to start the Mosquitto MQTT broker.
To discover local RuuviTag sensors broadcasting on local bluetooth, run the RuviTag Discoverer script.

## RuuviTag Discoverer
The script `ruvitag_discoverer.py` can be executed to discover RuuviTag sensors.

Executing the script:
```BASH
poetry run python ruvitag_discoverer.py --timeout=20 --no-print-mac --no-print-data
```
will provide a set of discovered mac addresses of RuuviTag sensors, broadcasting on nearby bluetooth.


## Telegraf
Telegraf is a server-based agent can collect and sends metrics and events for a diverse range of sources and sinks.

To start an instance of Telegraf, provide a configuration file:
```BASH
telegraf --config telegraf.conf
```

To run telegraf with multiple configuration files, specify config directory:
```BASH
telegraf --config-directory /path/to/telegraf.d
```

## Mosquitto MQTT broker

install the Mosquitto MQTT broker, and start the broker:
```BASH
mosquitto
```
Mosquitto starts an MQTT broker that listens on `localhost:1883`.
You may use the `mosquitto_sub` command to subscribe to topic messages. For example:
```BASH
mosquitto_sub -t 'telegraf/ruuvi/#'
```
