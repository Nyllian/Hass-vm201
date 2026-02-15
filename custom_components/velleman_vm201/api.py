"""API Placeholder."""

from dataclasses import dataclass
from enum import StrEnum
import logging
from random import choice, randrange
from typing import Optional

from http.client import (HTTPConnection, HTTPResponse)
from base64 import b64encode
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)


class DeviceType(StrEnum):
    """Device types."""
    
    INPUT_SENSOR = "input"
    OUTPUT_SENSOR = "output"
    TEMP_SENSOR = "temp_sensor"
    DOOR_SENSOR = "door_sensor"
    OTHER = "other"


DEVICES = [
    {"id": 99, "type": DeviceType.TEMP_SENSOR},
    {"id": 99, "type": DeviceType.DOOR_SENSOR},
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

class VMDeviceInfo:
    """The device info details"""
    name: str
    manufacturer: str
    model: str
    version: str

class API:
    """Class for example API."""

    def __init__(self, host: str, user: Optional[str] = None, pwd: Optional[str] = None) -> None:
        """Initialise."""
        self.host = host
        self.user = user
        self.pwd = pwd
        self.connected: bool = False

    def get_request(self, method, url) -> HTTPResponse:
        """Get a request object"""
        req = HTTPConnection(self.host)

        # Check if there is a username / password - skip baseAuth
        if (self.user is not None) and (self.pwd is not None):
            token = b64encode(f"{self.user}:{self.pwd}".encode('utf-8')).decode("ascii")
            baseAuthToken = f'Basic {token}'
            baseHeaders = { 'Authorization' : baseAuthToken }
            req.request(method, url, headers=baseHeaders)
        else:
            req.request(method, url)
        
        return req.getresponse()

    @property
    def controller_name(self) -> str:
        """Return the name of the controller."""
        return "VM201" # self.host.replace(".", "_")

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

        htmlContent = BeautifulSoup(self.get_request("GET", "/names.html").read(), 'html.parser')
        _LOGGER.debug("get_devices called")

        return [
            Device(device_id=1, #el.find("input")["name"][-2:-1],
                device_unique_id=self.get_device_unique_id(
                    el.find("input")["name"][-2:-1],
                    el.getText()[0:el.getText().find(" ")].lower()
                ),
                device_type=el.getText()[0:el.getText().find(" ")].lower(),
                name=el.find("input")["value"], #.replace(" ", "_"),
                state=self.get_device_value(
                    el.find("input")["name"][-2:-1],
                    el.getText()[0:el.getText().find(" ")].lower()
                )
            )
            for el in htmlContent.select("div#content p:not([class])")
        ]
    
    def update_device_states(self, devices: list[Device]):
        """Update the device states"""
        htmlContent = BeautifulSoup(self.get_request("GET", "/cgi/status.cgi").read(), 'html.parser')

        for dev in devices:
            if dev.device_type == DeviceType.INPUT_SENSOR:
                # Buf in the firmware HTML code - the state of the input is within the parent element
                # i = int(dev.device_unique_id[-1:])
                # el = htmlContent.find_all("input", { "id" : i })[0]
                # dev.state = bool(int(el.getText()))
                dev.state = False
            if dev.device_type == DeviceType.OUTPUT_SENSOR:
                i = int(dev.device_unique_id[-1:])
                state = htmlContent.find("leds").find_all("led")[i].getText()
                dev.state = bool(int(state))

            _LOGGER.debug("Update DeviceStates for dev: %s", dev)

    def get_device_info(self) -> VMDeviceInfo:
        """Return the device info properties"""
        htmlContent = BeautifulSoup(self.get_request("GET", "/about.html").read(), 'html.parser')
        vmDeviceInfo = VMDeviceInfo()
        vmDeviceInfo.name = htmlContent.find("h2").getText()
        vmDeviceInfo.manufacturer = " ".join(htmlContent.find('div', { "id" : "footer" }).getText().split(" ")[-2:])
        vmDeviceInfo.model = htmlContent.find("h1").getText()
        vmDeviceInfo.version = htmlContent.find("p").getText().split(": ")[1]
        
        return vmDeviceInfo


    def get_device_unique_id(self, device_id: str, device_type: DeviceType) -> str:
        """Return a unique device id."""
        if device_type == DeviceType.DOOR_SENSOR:
            return f"{self.controller_name}_D{device_id}"
        if device_type == DeviceType.TEMP_SENSOR:
            return f"{self.controller_name}_T{device_id}"
        if device_type == DeviceType.INPUT_SENSOR:
            return f"{self.controller_name}_I{device_id}"
        if device_type == DeviceType.OUTPUT_SENSOR:
            return f"{self.controller_name}_O{device_id}"
        return f"{self.controller_name}_Z{device_id}"

    def get_device_name(self, device_id: str, device_type: DeviceType) -> str:
        """Return the device name."""
        if device_type == DeviceType.DOOR_SENSOR:
            return f"DoorSensor{device_id}"
        if device_type == DeviceType.TEMP_SENSOR:
            return f"TempSensor{device_id}"
        if device_type == DeviceType.INPUT_SENSOR:
            return f"InputSensor{device_id}"
        if device_type == DeviceType.OUTPUT_SENSOR:
            return f"OutputSensor{device_id}"
        return f"OtherSensor{device_id}"

    def get_device_value(self, device_id: str, device_type: DeviceType) -> int | bool:
        """Get device random value."""
        if device_type == DeviceType.DOOR_SENSOR:
            return choice([True, False])
        if device_type == DeviceType.TEMP_SENSOR:
            return randrange(15, 28)
        if device_type == DeviceType.INPUT_SENSOR:
            return False
        if device_type == DeviceType.OUTPUT_SENSOR:
            return False
        return randrange(1, 10)


class APIAuthError(Exception):
    """Exception class for auth error."""


class APIConnectionError(Exception):
    """Exception class for connection error."""
