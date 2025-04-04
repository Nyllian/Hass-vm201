"""Interfaces with the Velleman Integration sensors."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MyConfigEntry
from .api import Device, VMDeviceInfo, DeviceType
from .const import DOMAIN
from .coordinator import VellemanCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Binary Sensors."""
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: VellemanCoordinator = config_entry.runtime_data.coordinator
    deviceInfo: VMDeviceInfo = coordinator.data.deviceInfo

    # Enumerate all the binary sensors in your data value from your DataUpdateCoordinator and add an instance of your binary sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    binary_sensors = [
        ExampleBinarySensor(coordinator, device, deviceInfo)
        for device in coordinator.data.devices
        if device.device_type in [DeviceType.DOOR_SENSOR, DeviceType.INPUT_SENSOR, DeviceType.OUTPUT_SENSOR]
    ]

    # Create the binary sensors.
    async_add_entities(binary_sensors)


class ExampleBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Implementation of a sensor."""
    
    def __init__(self, coordinator: VellemanCoordinator, device: Device, deviceInfo: VMDeviceInfo) -> None:
        """Initialise sensor."""
        super().__init__(coordinator)
        self.device = device
        self.deviceInfo = deviceInfo
        self.device_id = device.device_id
        self.coordinator = coordinator

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        self.device = self.coordinator.get_device_by_unique_id(
            self.device.device_type, self.device_id, self.device.device_unique_id
        )
        _LOGGER.debug("Device: %s", self.device)
        self.async_write_ha_state()

    @property
    def device_class(self) -> str:
        """Return device class."""
        # https://developers.home-assistant.io/docs/core/entity/binary-sensor#available-device-classes
        return BinarySensorDeviceClass.DOOR

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        # Identifiers are what group entities into the same device.
        # If your device is created elsewhere, you can just specify the indentifiers parameter.
        # If your device connects via another device, add via_device parameter with the indentifiers of that device.

        return DeviceInfo(
            # name=f"ExampleDevice{self.device.device_id}",
            name=self.deviceInfo.name,
            manufacturer=self.deviceInfo.manufacturer,
            model=self.deviceInfo.model,
            sw_version=self.deviceInfo.version,
            identifiers={
                (
                    DOMAIN,
                    f"{self.coordinator.data.controller_name}-{self.device.device_id}",
                )
            },
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.device.name

    @property
    def is_on(self) -> bool | None:
        """Return if the binary sensor is on."""
        # This needs to enumerate to true or false
        return self.device.state

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.device.device_unique_id}"

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        # Add any additional attributes you want on your sensor.
        attrs = {}
        attrs["extra_info"] = "Extra Info"
        return attrs
