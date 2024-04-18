import configparser
import os
from enum import Enum

"""
Allows an easy access to the global configuration parameters
and environmental variables
"""

PATH_TO_CONFIG = "environment_and_configuration/config.cfg"


class ConfigGroups(Enum):
    GENERIC = "generic"
    FRONTEND = "frontend"
    BACKEND = "backend"
    API = "api"


config = configparser.ConfigParser()
config.read(PATH_TO_CONFIG)


def get_environment_variable(
    key: str, optional: bool = False, default=None
) -> str | None:
    """Loads an environment variable

    Args:
        key (str): key of the variable
        optional (bool, optional):
            whether an exception shall be raised if not available.
            Defaults to False.
        default (_type_, optional): Default value if optional is True.
            Defaults to None.

    Returns:
        str | None: the value or None

    Raises:
        EnvironmentalVariableNotFoundError: if not optional but key not found
    """

    value: str | None = os.getenv(key, default=None)

    if value is None:
        if optional:
            value = default
        else:
            raise Exception(
                "The environmental variable "
                "{key} is not available but set to required!"
            )

    return value


def get_environment_variable_int(
    key: str, optional: bool = False, default=None
) -> int | None:
    """Loads an environment variable

    Args:
        key (str): key of the variable
        optional (bool, optional):
            whether an exception shall be raised if not available.
            Defaults to False.
        default (_type_, optional):
            Defaul value if optional is True.
            Defaults to None.

    Returns:
        int | None: the value or None

    Raises:
        EnvironmentalVariableNotFoundError: if not optional but key not found
    """
    return int(get_environment_variable(key, optional, default))


def get_environment_variable_bool(
    key: str, optional: bool = False, default=None
) -> bool | None:
    """Loads an environment variable

    Args:
        key (str): key of the variable
        optional (bool, optional):
            whether an exception shall be raised if not available.
            Defaults to False.
        default (_type_, optional):
            Defaul value if optional is True.
            Defaults to None.

    Returns:
        bool | None: the value or None

    Raises:
        EnvironmentalVariableNotFoundError: if not optional but key not found
    """
    env_var = get_environment_variable(key, optional, default)

    return env_var == "True" or env_var == "true" or env_var == "t" or env_var == "TRUE"


def get_configuration(group: ConfigGroups, key: str):
    return config[group.value][key]


def get_configuration_int(group: ConfigGroups, key: str):
    return int(config[group.value][key])


def get_configuration_float(group: ConfigGroups, key: str):
    return float(config[group.value][key])
