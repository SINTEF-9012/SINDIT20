# Connectors
Theese are the supported data connectors

## MQTT Connector

Example usage of the MQTT connector:
```python
connector = MQTTConnector()
connector.start()  # Start the MQTT client in separate thread
connector.subscribe("sensor/temperature")
# connector.subscribe("sensor/#")  # subscribe to wildcard

messages = connector.get_messages()  # get messages
connector.stop()    # stop the connector gracefully
```

Convert timestamp to datetime:
```python
for t in messages['sensor/temperature']['timestamp']:
    print(datetime.datetime.fromtimestamp(t))
```

## InfluxDB Connector

```python
import os
from dotenv import load_dotenv
load_dotenv('path/to/.env')
client = InfluxDBConnector(token=os.environ['INFLUX_ACCESS_TOKEN'])
client.connect()
buckets = client.get_bucket_names()
bucket = 'ruuvitag'
client.set_bucket(bucket=bucket)
tags = client.get_tags()
fields = client.get_fields()
field = 'humidity'
df = client.query_field(field=field, query_return_type='pandas')
df.plot(x='_time', y=field, kind='line')
client.disconnect()
```

![Image](../docs/img/humidity_output.png)


## S3Connector

For testing using a local minio instance. Start a minio docker container:

```bash
docker run -p 9000:9000 -p 9001:9001 \
  quay.io/minio/minio server /data --console-address ":9001"
```
This will spin up a docker container with minio. The container exposes the 9000 port for API connection and 9001 for managing minio through a frontend. The minio instance will have default credentials.

Using the S3Connector:
```python
from connectors.s3_connector import S3Connector
s3 = S3Connector(host="http://localhost", port=9000)
s3.start(no_update_connection_status=True)
s3.create_bucket('my-bucket')

## upload an object throught the client
with open('test.jpg', 'rb') as data:
    s3.put_object(bucket='my-bucket', key='key-of-object', data=data)

## upload an object using a presigned url
response = s3.create_presigned_url_for_upload_object(bucket='my-bucket', key='my-object')

import requests
with open(object_name, 'rb') as f:
    files = {'file': (object_name, f)}
    http_response = requests.post(response['url'], data=response['fields'], files=files)


## download an object using presigned url
response = s3.create_presigned_url_for_download_objec('my-bucket', 'my-object')

import requests
http_response = requests.get(response)

# stop the client
s3.stop(no_update_connection_status=True)
```
