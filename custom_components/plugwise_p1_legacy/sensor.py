""" P1-legacy sensor module."""

import logging
from datetime import timedelta
import voluptuous as vol
import requests
from lxml import etree

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_RESOURCES
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

from .api import SmileP1Api

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

SENSOR_PREFIX = "P1 "
SENSOR_TYPES = {
    "electricity_consumed_point": [
        "Electricity Consumed Point",
        "power",
        "W",
        "mdi:flash",
    ],
    "electricity_produced_point": [
        "Electricity Produced Point",
        "power",
        "W",
        "mdi:flash",
    ],
    "electricity_consumed_offpeak_interval": [
        "Electricity Consumed Off Peak Interval",
        "energy",
        "Wh",
        "mdi:flash",
    ],
    "electricity_consumed_peak_interval": [
        "Electricity Consumed Peak Interval",
        "energy",
        "Wh",
        "mdi:flash",
    ],
    "electricity_consumed_offpeak_cumulative": [
        "Electricity Consumed Off Peak Cumulative",
        "energy",
        "Wh",
        "mdi:flash",
    ],
    "electricity_consumed_peak_cumulative": [
        "Electricity Consumed Peak Cumulative",
        "energy",
        "Wh",
        "mdi:flash",
    ],
    "electricity_produced_offpeak_interval": [
        "Electricity Produced Off Peak Interval",
        "energy",
        "Wh",
        "mdi:white-balance-sunny",
    ],
    "electricity_produced_peak_interval": [
        "Electricity Produced Peak Interval",
        "energy",
        "Wh",
        "mdi:white-balance-sunny",
    ],
    "electricity_produced_offpeak_cumulative": [
        "Electricity Produced Off Peak Cumulative",
        "energy",
        "Wh",
        "mdi:white-balance-sunny",
    ],
    "electricity_produced_peak_cumulative": [
        "Electricity Produced Peak Cumulative",
        "energy",
        "Wh",
        "mdi:white-balance-sunny",
    ],
    "net_electricity_cumulative": [
        "Net Electricity Cumulative",
        "power",
        "W",
        "mdi:flash",
    ],
    "net_electricity_point": ["Net Electricity Point", "power", "W", "mdi:flash"],
    "gas_consumed_interval": ["Gas Consumed Interval", None, "m3", "mdi:gas-cylinder"],
    "gas_consumed_cumulative": [
        "Gas Consumed Cumulative",
        None,
        "m3",
        "mdi:gas-cylinder",
    ],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_RESOURCES, default=[]): vol.All(
            cv.ensure_list, [vol.In(SENSOR_TYPES)]
        ),
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the Plugwise Smile sensors."""
    host = config.get(CONF_HOST)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    try:
        data = PlugwiseSmileData(host, username, password)
    except RunTimeError:
        _LOGGER.error("Unable to connect fetch data from Plugwise Smile %s", host)
        return False

    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type not in SENSOR_TYPES:
            SENSOR_TYPES[sensor_type] = [sensor_type.title(), "", "mdi:flash"]

        entities.append(PlugwiseSmileSensor(data, sensor_type))

    add_entities(entities)


# pylint: disable=abstract-method
class PlugwiseSmileData(object):
    """Representation of a Plugwise Wise."""

    def __init__(self, host, username, password):
        """Initialize the Plugwise Smile data."""
        self._host = host
        self._username = username
        self._password = password
        self._api = SmileP1Api(self._host, self._username, self._password)
        self._electricity_module = None
        self._gas_module = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the data from the server."""
        self._electricity_module = self._api.get_electricity_module()
        self._gas_module = self._api.get_gas_module()

    def get_electricity_consumed_point(self):
        return self._api.get_electricity_consumed_point(self._electricity_module)

    def get_electricity_consumed_offpeak_interval(self):
        return self._api.get_electricity_consumed_offpeak_interval(
            self._electricity_module
        )

    def get_electricity_consumed_peak_interval(self):
        return self._api.get_electricity_consumed_peak_interval(
            self._electricity_module
        )

    def get_electricity_consumed_offpeak_cumulative(self):
        return self._api.get_electricity_consumed_offpeak_cumulative(
            self._electricity_module
        )

    def get_electricity_consumed_peak_cumulative(self):
        return self._api.get_electricity_consumed_peak_cumulative(
            self._electricity_module
        )

    def get_electricity_produced_point(self):
        return self._api.get_electricity_produced_point(self._electricity_module)

    def get_electricity_produced_offpeak_interval(self):
        return self._api.get_electricity_produced_offpeak_interval(
            self._electricity_module
        )

    def get_electricity_produced_peak_interval(self):
        return self._api.get_electricity_produced_peak_interval(
            self._electricity_module
        )

    def get_electricity_produced_offpeak_cumulative(self):
        return self._api.get_electricity_produced_offpeak_cumulative(
            self._electricity_module
        )

    def get_electricity_produced_peak_cumulative(self):
        return self._api.get_electricity_produced_peak_cumulative(
            self._electricity_module
        )

    def get_gas_consumed_interval(self):
        return self._api.get_gas_consumed_interval(self._gas_module)

    def get_gas_consumed_cumulative(self):
        return self._api.get_gas_consumed_cumulative(self._gas_module)


class PlugwiseSmileSensor(Entity):
    """Representation of a Plugwise Smile sensor."""

    def __init__(self, data, sensor_type):
        """Initialize the sensor."""
        self.data = data
        self.sr_type = sensor_type
        self._name = SENSOR_PREFIX + SENSOR_TYPES[self.sr_type][0]
        self._device_class = SENSOR_TYPES[self.sr_type][1]
        self._unit_of_measurement = SENSOR_TYPES[self.sr_type][2]
        self._icon = SENSOR_TYPES[self.sr_type][3]
        self._state = None

        self.update()

    @property
    def device_class(self):
        """Return the device_class of the sensor."""
        return self._device_class

    @property
    def entity_registry_enabled_default(self):
        """Return if the entity should be enabled when first added to the entity registry."""
        return True

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    def update(self):
        """Get the latest data and use it to update our sensor state."""
        self.data.update()

        if self.sr_type == "electricity_consumed_point":
            self._state = self.data.get_electricity_consumed_point()
        if self.sr_type == "electricity_produced_point":
            self._state = self.data.get_electricity_produced_point()
        if self.sr_type == "electricity_consumed_offpeak_interval":
            self._state = self.data.get_electricity_consumed_offpeak_interval()
        if self.sr_type == "electricity_consumed_peak_interval":
            self._state = self.data.get_electricity_consumed_peak_interval()
        if self.sr_type == "electricity_consumed_offpeak_cumulative":
            self._state = self.data.get_electricity_consumed_offpeak_cumulative()
        if self.sr_type == "electricity_consumed_peak_cumulative":
            self._state = self.data.get_electricity_consumed_peak_cumulative()
        if self.sr_type == "electricity_produced_offpeak_interval":
            self._state = self.data.get_electricity_produced_offpeak_interval()
        if self.sr_type == "electricity_produced_peak_interval":
            self._state = self.data.get_electricity_produced_peak_interval()
        if self.sr_type == "electricity_produced_offpeak_cumulative":
            self._state = self.data.get_electricity_produced_offpeak_cumulative()
        if self.sr_type == "electricity_produced_peak_cumulative":
            self._state = self.data.get_electricity_produced_peak_cumulative()
        if self.sr_type == "gas_consumed_interval":
            self._state = self.data.get_gas_consumed_interval()
        if self.sr_type == "gas_consumed_cumulative":
            self._state = self.data.get_gas_consumed_cumulative()
        if self.sr_type == "net_electricity_point":
            self._state = (
                self.data.get_electricity_consumed_point()
                - self.data.get_electricity_produced_point()
            )
        if self.sr_type == "net_electricity_cumulative":
            self._state = (
                self.data.get_electricity_consumed_offpeak_cumulative()
                + self.data.get_electricity_consumed_peak_cumulative()
                - self.data.get_electricity_produced_offpeak_cumulative()
                - self.data.get_electricity_produced_peak_cumulative()
            )
