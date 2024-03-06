import datetime

import requests

print("Hello world!")
print("The current time is", datetime.datetime.now())


def greet(name: str) -> str:
    """Greet someone by their name."""
    if name == "":
        name = "World"
    return f"Hello, {name}!"


def check_vg_connection():
    response = requests.get("https://www.vg.no")
    print(f"status code VG: {response.status_code}")
    return response.status_code
