import asyncio

import pytest
from ruuvitag.ruuvitag_datacollector import get_data_async
from ruuvitag.ruuvitag_discoverer import discover_sensors


# Create a mock args object
class Args:
    timeout = 1
    no_print_mac = True
    no_print_data = True


@pytest.mark.gitlab_exempt
@pytest.mark.ble
@pytest.mark.asyncio
async def test_discover_sensors(mocker):
    # Mock the RuuviTagSensor.get_data_async method
    mocker.patch(
        "ruuvitag_sensor.ruuvi.RuuviTagSensor.get_data_async",
        return_value=asyncio.as_completed([]),
    )
    # Mock the update_progress_bar function
    mocker.patch(
        "ruuvitag.ruuvitag_discoverer.update_progress_bar",
        return_value=asyncio.sleep(0),
    )
    args = Args()
    # Call the discover_sensors function
    await discover_sensors(args)


@pytest.mark.gitlab_exempt
@pytest.mark.ble
@pytest.mark.asyncio
async def test_ruuvitag_datacollector(mocker):
    # Mock asyncio.sleep to avoid the RuntimeWarning
    mocker.patch("asyncio.sleep", return_value=asyncio.Future())
    await get_data_async([])
