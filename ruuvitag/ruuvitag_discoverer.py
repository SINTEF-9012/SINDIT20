import argparse
import asyncio

from ruuvitag_sensor.ruuvi import RuuviTagSensor
from tqdm.asyncio import tqdm


def parse_args():
    parser = argparse.ArgumentParser()
    parser.description = "Discover and print data from RuuviTag sensors"
    parser.add_argument(
        "--no-print-mac",
        action="store_true",
        default=False,
        help="Do not print the MAC address of the sensors",
    )
    parser.add_argument(
        "--no-print-data",
        action="store_true",
        default=False,
        help="Do not print the captured sensor data",
    )
    parser.add_argument(
        "--macs",
        nargs="+",
        help="""List of MAC addresses of the sensors.
        If empty, data will be collected for all found sensors""",
    )
    parser.add_argument(
        "--timeout", type=int, default=10, help="Timeout for discovering sensors"
    )
    return parser.parse_args()


async def update_progress_bar(pbar, timeout):
    for _ in range(timeout):
        await asyncio.sleep(1)
        pbar.update(1)


async def discover_sensors(args):
    list_of_macs = []
    try:
        async with asyncio.timeout(args.timeout + 1):
            with tqdm(total=args.timeout, desc="Discovering sensors", unit="s") as pbar:
                try:
                    progress_task = asyncio.create_task(
                        update_progress_bar(pbar, args.timeout)
                    )
                    async for found_data in RuuviTagSensor.get_data_async(args.macs):
                        if not args.no_print_mac:
                            print(found_data[0])
                        if not args.no_print_data:
                            print(found_data[1])
                        list_of_macs.append(found_data[0])
                        await progress_task
                except asyncio.exceptions.CancelledError:
                    discovered_macs = set(list_of_macs)
                    print(
                        f"""\n
Timeout reached while discovering sensors.
List of discovered mac addresses:
{discovered_macs}
"""
                    )
    except Exception as error:
        print(f"An unexpected error occurred: {error}")


async def main():
    args = parse_args()
    await discover_sensors(args)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
