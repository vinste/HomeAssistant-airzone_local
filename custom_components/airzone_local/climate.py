import logging
from typing import Any, Dict, List, Optional
from datetime import timedelta
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE
from homeassistant.util.temperature import convert as convert_temperature
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODES,
    SUPPORT_TARGET_TEMPERATURE,
)

# init logger
_LOGGER = logging.getLogger(__name__)

# default refresh interval
SCAN_INTERVAL = timedelta(seconds=60)

AIRZONECLOUD_ZONE_HVAC_MODES = [
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
]


import requests
import json


class AirzoneLocal:
    """Allow to connect to AirzoneCloudLocal API"""

    _attrs = {}
    _zones = []
    _id = 2  # Master ID (internal value but can be extracted from the one with "modes")

    def __init__(self, ip):
        self._ip = ip
        self._zones = self._load()

    @property
    def name(self):
        return "system_{}".format(self._zones[self._id].get("systemID"))

    @property
    def mode(self):
        return self._zones[self._id].get("mode")

    @property
    def current_temperature(self):
        return round(self._zones[self._id].get("roomTemp"), 1)

    @property
    def current_humidity(self):
        return self._zones[self._id].get("humidity")

    @property
    def target_temperature(self):
        return self._zones[self._id].get("setpoint")

    @property
    def max_temp(self):
        return self._zones[self._id].get("maxTemp")

    @property
    def min_temp(self):
        return self._zones[self._id].get("minTemp")

    @property
    def is_on(self):
        return bool(int(self._data.get("state", 0)))

    @property
    def attrs(self):
        return self._attrs

    def set_mode(self, mode):
        _LOGGER.info("set_mode ({}) NOT IMPLEMENTED".format(mode))
        return -1

    def turn_on(self, mode):
        _LOGGER.info("turn_on NOT IMPLEMENTED")
        return -1

    def turn_off(self, mode):
        _LOGGER.info("turn_off NOT IMPLEMENTED")
        return -1

    def set_temperature(self, temp):
        _LOGGER.info("set_temperature ({}) NOT IMPLEMENTED".format(temp))
        return -1

    def refresh(self):
        """Refresh devices"""
        self._load()

    def _load(self):
        url = "http://" + self._ip + ":3000/api/v1/hvac"
        self._zones = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data='{"systemid":1,"zoneid":0}',
        ).json()["data"]

        for i, z in enumerate(self._zones):
            self._attrs["room_temp_{}".format(i + 1)] = round(z.get("roomTemp"), 1)
            err = z.get("errors")
            if len(err) == 0:
                self._attrs["errors"] = "None"
            else:
                self._attrs["errors"] = str(err)

        return self._zones


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the AirzonecloudLocal platform"""
    ip = config.get("ip")

    api = None
    try:
        api = AirzoneLocal(ip)
    except Exception as err:
        _LOGGER.error(err)
        hass.services.call(
            "persistent_notification",
            "create",
            {"title": "AirzoneLocal error", "message": str(err)},
        )
        return

    entities = []
    entities.append(AirzoneSystem(api))
    add_entities(entities)


class AirzoneSystem(ClimateEntity):
    """Representation of an Airzonecloud System"""

    hidden = True  # default hidden
    _api = None

    def __init__(self, api):
        """Initialize the system"""
        self._api = api
        _LOGGER.info("init airzone {}".format(self._api.name))

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._api.name

    @property
    def unique_id(self) -> Optional[str]:
        """Return a unique ID."""
        return self._api.name

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def hvac_modes(self) -> List[str]:
        """Return the list of available hvac operation modes."""
        return AIRZONECLOUD_ZONE_HVAC_MODES

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation ie. heat, cool mode."""
        mode = self._api.mode

        if mode == 2:
            return HVAC_MODE_OFF

        if mode == 2:
            return HVAC_MODE_COOL

        if mode == 3:
            return HVAC_MODE_HEAT

        if mode == 4:
            return HVAC_MODE_FAN_ONLY

        if mode == 5:
            return HVAC_MODE_DRY

        return HVAC_MODE_OFF

    @property
    def current_humidity(self) -> Optional[float]:
        """Return the current humidity."""
        return self._api.current_humidity

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return self._api.current_temperature

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the temperature we try to reach."""
        return self._api.target_temperature

    @property
    def target_temperature_step(self) -> Optional[float]:
        """Return the supported step of target temperature."""
        return 0.5

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return self._api.attrs

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return convert_temperature(
            self._api.min_temp, TEMP_CELSIUS, self.temperature_unit
        )

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return convert_temperature(
            self._api.max_temp, TEMP_CELSIUS, self.temperature_unit
        )

    def set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        _LOGGER.info("set_hvac_mode ({})".format(hvac_mode))
        if hvac_mode == HVAC_MODE_OFF:
            self._api.set_mode(1)
        elif hvac_mode == HVAC_MODE_COOL:
            self._api.set_mode(2)
        elif hvac_mode == HVAC_MODE_HEAT:
            self._api.set_mode(3)
        elif hvac_mode == HVAC_MODE_FAN_ONLY:
            self._api.set_mode(4)
        elif hvac_mode == HVAC_MODE_DRY:
            self._api.set_mode(5)

    def turn_on(self):
        """Turn on."""
        self._api.turn_on()

    def turn_off(self):
        """Turn off."""
        self._api.turn_off()

    def set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            self._api.set_temperature(round(float(temperature), 1))

    def update(self):
        self._api.refresh()
