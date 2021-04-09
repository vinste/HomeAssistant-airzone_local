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



class AirzoneCloudLocal:
    """Allow to connect to AirzoneCloudLocal API"""

    _zones = []

    def __init__(self, ip):

        self._ip = ip

        self._load_all()

    @property
    def system(self):
        """Get system info"""
        return self.system

    @property
    def all_zones(self):
        """Get all zones from all devices (same order as in app)"""
        return self.zones

    #
    # Refresh
    #
    def refresh_devices(self):
        """Refresh devices"""
        self._load_devices()

        

    def _login(self):
        """Login to AirzoneCloud and return token"""

        try:
            url = "{}{}".format(self._base_url, API_LOGIN)
            login_payload = {"email": self._username, "password": self._password}
            headers = {"User-Agent": self._user_agent}
            response = self._session.post(
                url, headers=headers, json=login_payload
            ).json()
            self._token = response.get("user").get("authentication_token")
        except (RuntimeError, AttributeError):
            raise Exception("Unable to login to AirzoneCloud") from None

        _LOGGER.info("Login success as {}".format(self._username))

        return self._token

    def _load_all(self):
        """Load all devices for this account"""
        current_devices = self._devices
        self._devices = []
        try:
            for device_relation in self._get_device_relations():
                device_data = device_relation.get("device")
                device = None
                # search device in current_devices (if where are refreshing devices)
                for current_device in current_devices:
                    if current_device.id == device_data.get("id"):
                        device = current_device
                        device._set_data_refreshed(device_data)
                        break
                # device not found => instance new device
                if device is None:
                    device = Device(self, device_data)
                self._devices.append(device)
        except RuntimeError:
            raise Exception("Unable to load devices from AirzoneCloud")
        return self._devices

    def _get_device_relations(self):
        """Http GET to load devices"""
        _LOGGER.debug("get_device_relations()")
        return self._get(API_DEVICE_RELATIONS).get("device_relations")

    def _get_systems(self, device_id):
        """Http GET to load systems"""
        _LOGGER.debug("get_systems(device_id={})".format(device_id))
        return self._get(API_SYSTEMS, {"device_id": device_id}).get("systems")

    def _get_zones(self, system_id):
        """Http GET to load Zones"""
        _LOGGER.debug("get_zones(system_id={})".format(system_id))
        return self._get(API_ZONES, {"system_id": system_id}).get("zones")

    def _send_event(self, payload):
        """Http POST to send an event"""
        _LOGGER.debug("Send event with payload: {}".format(json.dumps(payload)))
        try:
            result = self._post(API_EVENTS, payload)
            _LOGGER.debug("Result event: {}".format(json.dumps(result)))
            return result
        except RuntimeError:
            _LOGGER.error("Unable to send event to AirzoneCloud")
            return None

    def _get(self, api_endpoint, params={}):
        """Do a http GET request on an api endpoint"""
        params["format"] = "json"

        return self._request(method="GET", api_endpoint=api_endpoint, params=params)

    def _post(self, api_endpoint, payload={}):
        """Do a http POST request on an api endpoint"""
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
        }

        return self._request(
            method="POST", api_endpoint=api_endpoint, headers=headers, json=payload
        )

    def _request(
        self, method, api_endpoint, params={}, headers={}, json=None, autoreconnect=True
    ):
        # generate url with auth
        params["user_email"] = self._username
        params["user_token"] = self._token
        url = "{}{}/?{}".format(
            self._base_url, api_endpoint, urllib.parse.urlencode(params)
        )

        # set user agent
        headers["User-Agent"] = self._user_agent

        # make call
        call = self._session.request(method=method, url=url, headers=headers, json=json)

        if call.status_code == 401 and autoreconnect:  # unauthorized error
            # log
            _LOGGER.info(
                "Get unauthorized error (token expired ?), trying to reconnect..."
            )

            # try to reconnect
            self._login()

            # retry get without autoreconnect (to avoid infinite loop)
            return self._request(
                method=method,
                api_endpoint=api_endpoint,
                params=params,
                headers=headers,
                json=json,
                autoreconnect=False,
            )

        # raise other error if needed
        call.raise_for_status()

        return call.json()
    
    
    


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the AirzonecloudLocal platform"""
    ip = config.get("ip")
    
    api = None
    try:
        api = AirzoneCloudLocal(ip)
    except Exception as err:
        _LOGGER.error(err)
        hass.services.call(
            "persistent_notification",
            "create",
            {"title": "AirzoneCloudLocal error", "message": str(err)},
        )
        return

    entities = []
    for device in api.devices:
        for system in device.systems:
            # add zones
            for zone in system.zones:
                entities.append(AirzonecloudZone(zone))
            # add system to allow grouped update on all sub zones
            entities.append(AirzonecloudSystem(system))

    add_entities(entities)


class AirzonecloudZone(ClimateEntity):
    """Representation of an Airzonecloud Zone"""

    def __init__(self, data, master, id):
        """Initialize the zone"""
        self._data = data
        self._master = master
        self._id = id
        _LOGGER.info("init zone {} ({})".format(self.name, self.unique_id))

    @property
    def unique_id(self) -> Optional[str]:
        """Return a unique ID."""
        return "zone_{}_{}".format(self..get("zoneID")

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Zone_{}_{}".format(self._data.get("systemID"), self._data.get("zoneID")

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation ie. heat, cool mode."""
        mode = self._azc_zone.mode

        if self._azc_zone.is_on:
            if mode in ["cool-air", "cool-radiant", "cool-both"]:
                return HVAC_MODE_COOL

            if mode in ["heat-air", "heat-radiant", "heat-both"]:
                return HVAC_MODE_HEAT

            if mode == "ventilate":
                return HVAC_MODE_FAN_ONLY

            if mode == "dehumidify":
                return HVAC_MODE_DRY

        return HVAC_MODE_OFF

    @property
    def hvac_modes(self) -> List[str]:
        """Return the list of available hvac operation modes."""
        return AIRZONECLOUD_ZONE_HVAC_MODES

    @property
    def current_humidity(self) -> Optional[float]:
        """Return the current humidity."""
        return self._azc_zone.current_humidity

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return self._azc_zone.current_temperature

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the temperature we try to reach."""
        return self._azc_zone.target_temperature

    @property
    def target_temperature_step(self) -> Optional[float]:
        """Return the supported step of target temperature."""
        return 0.5

    def set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            self._azc_zone.set_temperature(round(float(temperature), 1))

    def set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVAC_MODE_OFF:
            self.turn_off()
        else:
            if not self._azc_zone.is_on:
                self.turn_on()

            # set hvac mode on parent system
            if hvac_mode == HVAC_MODE_HEAT:
                self._azc_zone.system.set_mode("heat-both")
            elif hvac_mode == HVAC_MODE_COOL:
                self._azc_zone.system.set_mode("cool-both")
            elif hvac_mode == HVAC_MODE_DRY:
                self._azc_zone.system.set_mode("dehumidify")
            elif hvac_mode == HVAC_MODE_FAN_ONLY:
                self._azc_zone.system.set_mode("ventilate")

    def turn_on(self):
        """Turn on."""
        self._azc_zone.turn_on()

    def turn_off(self):
        """Turn off."""
        self._azc_zone.turn_off()

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return convert_temperature(
            self._azc_zone.system.min_temp, TEMP_CELSIUS, self.temperature_unit
        )

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return convert_temperature(
            self._azc_zone.system.max_temp, TEMP_CELSIUS, self.temperature_unit
        )


class AirzonecloudSystem(ClimateEntity):
    """Representation of an Airzonecloud System"""

    hidden = True  # default hidden

    def __init__(self, azc_system):
        """Initialize the system"""
        self._azc_system = azc_system
        _LOGGER.info("init system {} ({})".format(self.name, self.unique_id))

    @property
    def unique_id(self) -> Optional[str]:
        """Return a unique ID."""
        return "system_" + self._azc_system.id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._azc_system.name

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation ie. heat, cool mode."""
        mode = self._azc_system.mode

        if mode in ["cool-air", "cool-radiant", "cool-both"]:
            return HVAC_MODE_COOL

        if mode in ["heat-air", "heat-radiant", "heat-both"]:
            return HVAC_MODE_HEAT

        if mode == "ventilate":
            return HVAC_MODE_FAN_ONLY

        if mode == "dehumidify":
            return HVAC_MODE_DRY

        return HVAC_MODE_OFF

    @property
    def hvac_modes(self) -> List[str]:
        """Return the list of available hvac operation modes."""
        return AIRZONECLOUD_ZONE_HVAC_MODES

    def set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVAC_MODE_OFF:
            self._azc_system.set_mode("stop")
        if hvac_mode == HVAC_MODE_HEAT:
            self._azc_system.set_mode("heat-both")
        elif hvac_mode == HVAC_MODE_COOL:
            self._azc_system.set_mode("cool-both")
        elif hvac_mode == HVAC_MODE_DRY:
            self._azc_system.set_mode("dehumidify")
        elif hvac_mode == HVAC_MODE_FAN_ONLY:
            self._azc_system.set_mode("ventilate")

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return 0

    def update(self):
        self._azc_system.refresh(True)
