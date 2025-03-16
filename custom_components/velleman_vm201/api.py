"""API Placeholder."""

from dataclasses import dataclass
from enum import StrEnum
import logging
from random import choice, randrange

from http.client import HTTPConnection
from http.client import HTTPResponse
from base64 import b64encode
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)


class DeviceType(StrEnum):
    """Device types."""
    INPUT = "input"
    OUTPUT = "output"
    TEMP_SENSOR = "temp_sensor"
    DOOR_SENSOR = "door_sensor"
    OTHER = "other"


DEVICES = [
    {"id": 1, "type": DeviceType.TEMP_SENSOR},
    {"id": 1, "type": DeviceType.DOOR_SENSOR},
]


@dataclass
class Device:
    """API device."""
    # name - value of the element (this can change...)

    device_id: int
    device_unique_id: str
    device_type: DeviceType
    name: str
    state: int | bool


class API:
    """Class for example API."""

    def __init__(self, host: str, user: str, pwd: str) -> None:
        """Initialise."""
        self.host = host
        self.user = user
        self.pwd = pwd
        self.connected: bool = False

    @property
    def controller_name(self) -> str:
        """Return the name of the controller."""
        return self.host.replace(".", "_")

    def get_request(self, method, url) -> HTTPResponse:
        """Get a request object"""
        token = b64encode(f"{self.user}:{self.pwd}".encode('utf-8')).decode("ascii")
        baseAuthToken = f'Basic {token}'

        req = HTTPConnection(self.host)
        baseHeaders = { 'Authorization' : baseAuthToken }
        req.request(method, url, headers=baseHeaders)
        return req.getresponse()

    def connect(self) -> bool:
        """Connect to api."""
        # Connect to the VM201 board
        res = self.get_request("GET", "/")
        
        if res.code == 200:
            self.connected = True
            return True
        raise APIAuthError("Error connecting to api. Invalid username or password.")

    def disconnect(self) -> bool:
        """Disconnect from api."""
        self.connected = False
        return True

    def get_devices(self) -> list[Device]:
        """Get devices on api."""
        # Do an API call te retrieve all the devices
        # 8 Output switches (type should be configurable?)
        #    As there are on_off switches
        #    As there are toggle switches
        # 8 Output sensors (state of switch)
        # 1 Input sensor

        devices = []
        htmlContent = BeautifulSoup(self.get_request("GET", "/names.html").read(), 'html.parser')
        for el in htmlContent.select("div#content p:not([class])"):
            devId = el.find("input")["name"][-2:-1]
            devType = el.getText()[0:el.getText().find(" ")].lower()
            devName = el.find("input")["value"].replace(" ", "_")

            devices.append(
                Device(device_id=devId,
                   device_unique_id=self.get_device_unique_id(devId, devType),
                   device_type=devType,
                   name=devName
                )
            )
            #el.find("input")["name"].replace("[", ".").replace("]", "")
            #el.find("input")["value"].replace(" ", "_")
            #el.find("input")["name"][-2:-1]

        return devices

        #This will return an array of all the devices
        return [
            Device(
                device_id=device.get("id"),
                device_unique_id=self.get_device_unique_id(
                    device.get("id"), device.get("type")
                ),
                device_type=device.get("type"),
                name=self.get_device_name(device.get("id"), device.get("type")),
                state=self.get_device_value(device.get("id"), device.get("type")),
            )
            for device in DEVICES
        ]

    def get_device_unique_id(self, device_id: str, device_type: DeviceType) -> str:
        """Return a unique device id."""
        if device_type == DeviceType.DOOR_SENSOR:
            return f"{self.controller_name}_D{device_id}"
        if device_type == DeviceType.TEMP_SENSOR:
            return f"{self.controller_name}_T{device_id}"
        if device_type == DeviceType.INPUT:
            return f"{self.controller_name}_I{device_id}"
        if device_type == DeviceType.OUTPUT:
            return f"{self.controller_name}_O{device_id}"
        return f"{self.controller_name}_Z{device_id}"

    def get_device_name(self, device_id: str, device_type: DeviceType) -> str:
        """Return the device name."""
        if device_type == DeviceType.DOOR_SENSOR:
            return f"DoorSensor{device_id}"
        if device_type == DeviceType.TEMP_SENSOR:
            return f"TempSensor{device_id}"
        return f"OtherSensor{device_id}"

    def get_device_value(self, device_id: str, device_type: DeviceType) -> int | bool:
        """Get device random value."""
        if device_type == DeviceType.DOOR_SENSOR:
            return choice([True, False])
        if device_type == DeviceType.TEMP_SENSOR:
            return randrange(15, 28)
        return randrange(1, 10)


class APIAuthError(Exception):
    """Exception class for auth error."""


class APIConnectionError(Exception):
    """Exception class for connection error."""
