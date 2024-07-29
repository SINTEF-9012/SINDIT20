import asyncio

from ruuvitag_sensor.ruuvi import RuuviTagSensor

# List of MAC addresses of the sensors.
# If empty, data will be collected for all found sensors
# macs = ["C5:32:6C:6D:DD:3F"]
macs = []


def format_as_influx(data) -> str:
    # measurement name
    line = "ruuvi"
    # tags
    line += f",mac={data['mac']} "
    # add fields:
    for key, value in data.items():
        if key in ["mac", "data_format"]:
            continue
        line += f"{key}={value},"
    line = line[:-1]  # remove trailing comma
    return line


async def get_data_async(macs):
    datapoint = {}
    # TODO: How to handle multiple macs to send input data for telegraf?
    async for found_data in RuuviTagSensor.get_data_async(macs):
        datapoint = found_data[1]
        break  # NB! Breaks forloop after first datapoint!!!
    return datapoint


async def main():
    datapoint = await get_data_async(macs)
    print(format_as_influx(datapoint))


if __name__ == "__main__":
    asyncio.run(main())
