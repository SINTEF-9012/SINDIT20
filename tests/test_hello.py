# test_hello.py

from hello import check_vg_connection, greet


def test_greet():
    names = ["Neo", "Trinity", "Morpheous", "Agent Smith"]
    for name in names:
        assert greet(name) == f"Hello, {name}!"
    assert greet("") == "Hello, World!"


def test_check_vg_connection():
    assert check_vg_connection() == 200
