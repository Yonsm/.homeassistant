#!/usr/bin/env python3
# encoding: utf-8
import json
import socket
import select
import logging

# Bridge receive: b'\xaaO\x01UA\xf19\x8f\x0b\x00\x00\x00\x00\x00\x00\x00\x00\xb0\xf8\x93\x1f\x14U\x00Z\x00\x00\x02{"sleep":"1","startTime":82800,"endTime":21600,"type":1}\xff#END#'
# Bridge receive: b'\xaaO\x01UA\xf19\x8f\x0b\x00\x00\x00\x00\x00\x00\x00\x00\xb0\xf8\x93\x1f\x14U\x00>\x00\x00\x02{"brightness":"25","type":2}\xff#END#'
# Bridge receive: b'\xaaO\x01UA\xf19\x8f\x0b\x00\x00\x00\x00\x00\x00\x00\x00\xb0\xf8\x93\x1f\x14U\x007\x00\x00\x02{"type":5,"status":1}\xff#END#'

_LOGGER = logging.getLogger(__name__)


class AirCatData:
    """Class for handling the data retrieval."""

    def __init__(self):
        """Initialize the data object."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.settimeout(1)
        self._socket.bind(('', 9000))  # aircat.phicomm.com
        self._socket.listen(5)
        self._rlist = [self._socket]
        self._times = 0
        self.devs = {}

    def shutdown(self):
        """Shutdown."""
        if self._socket is not None:
            #_LOGGER.debug("Socket shutdown")
            self._socket.close()
            self._socket = None

    def loop(self):
        while True:
            self.update(None)  # None = wait forever

    def update(self, timeout=0):  # 0 = return right now
        rfd, wfd, efd = select.select(self._rlist, [], [], timeout)
        for fd in rfd:
            try:
                if fd is self._socket:
                    conn, addr = self._socket.accept()
                    _LOGGER.debug('Connected %s', addr)
                    self._rlist.append(conn)
                    conn.settimeout(1)
                else:
                    self.handle(fd)
            except:
                #import traceback
                #_LOGGER.error('Exception: %s', traceback.format_exc())
                pass

    def handle(self, conn):
        """Handle connection."""
        data = conn.recv(
            4096)  # If connection is closed, recv() will result a timeout exception and receive '' next time, so we can purge connection list
        if not data:
            _LOGGER.debug('Closed %s', conn)
            self._rlist.remove(conn)
            conn.close()
            return

        if data.startswith(b'GET'):
            _LOGGER.debug('Request from HTTP -->\n%s', data)
            conn.sendall(b'HTTP/1.0 200 OK\nContent-Type: text/json\n\n' +
                         json.dumps(self.devs, indent=2).encode('utf-8'))
            self._rlist.remove(conn)
            conn.close()
            return

        end = data.rfind(b'\xff#END#')
        payload = data.rfind(b'{', 0, end)

        self._times += 1
        if payload >= 11:
            mac = ''.join(['%02X' % (x if isinstance(x, int) else ord(x))
                           for x in data[payload-11:payload-5]])
            try:
                jsonStr = data[payload:end].decode('utf-8')
                attributes = json.loads(jsonStr)
                self.devs[mac] = attributes
                _LOGGER.debug('%d Received %s: %s',
                              self._times, mac, attributes)
            except:
                _LOGGER.error('%d Received invalid: %s', self._times, data)
        else:
            _LOGGER.debug('%d Received short payload: %s', self._times, data)

        response = self.response(data, payload, end)
        if response:
            _LOGGER.debug('  Response %s\n', response)
            conn.sendall(response)

    def response(self, data, payload, end):
        # begin(17) + mac(6)+size(5) + payload(0~) + end(6)
        if payload == -1 and end >= 28 and data[end-1] != (125 if isinstance(data[end-1], int) else '}'):
            _LOGGER.info('  Control message: %s', data)
            payload = end
            self._times = 0
        else:
            if self._times % 5 != 0:
                return None

        if payload >= 28:
            prefix = data[payload-28:payload-5]
        else:
            _LOGGER.error('  Invalid prefix: %s', data)
            #prefix = b'\xaaO\x01UA\xf19\x8f\x0b\x00\x00\x00\x00\x00\x00\x00\x00\xb0\xf8\x93\x1f\x14U'
            return None

        return prefix + b'\x00\x37\x00\x00\x02{"type":5,"status":1}\xff#END#'


class AirCatBridge(AirCatData):
    """Class for handling the data retrieval."""

    def __init__(self):
        """Initialize the data object."""
        super(AirCatBridge, self).__init__()
        self._phicomm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._phicomm.settimeout(5)
        self._phicomm.connect(('47.102.38.171', 9000))

    def shutdown(self):
        """Shutdown."""
        super(AirCatBridge, self).shutdown()
        if self._phicomm is not None:
            self._phicomm.close()
            self._phicomm = None

    def response(self, data, payload, end):
        print('  Bridge send: %s' % data)
        self._phicomm.sendall(data)
        try:
            response = self._phicomm.recv(4096)
            print('  Bridge receive: %s' % response)
            return response
        except:
            print('  Bridge receive: None!')
            return super(AirCatBridge, self).response(data, payload, end)


if __name__ == '__main__':
    _LOGGER.setLevel(logging.DEBUG)
    _LOGGER.addHandler(logging.StreamHandler())
    aircat = AirCatBridge()
    try:
        aircat.loop()
    except KeyboardInterrupt:
        pass
    aircat.shutdown()
    exit(0)


"""
Support for AirCat air sensor.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.aircat/
"""
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_NAME, CONF_MAC, CONF_SENSORS, TEMP_CELSIUS
from homeassistant.components.sensor import PLATFORM_SCHEMA
import voluptuous as vol


SENSOR_PM25 = 'pm25'
SENSOR_HCHO = 'hcho'
SENSOR_TEMPERATURE = 'temperature'
SENSOR_HUMIDITY = 'humidity'

DEFAULT_NAME = 'AirCat'
DEFAULT_SENSORS = [SENSOR_PM25, SENSOR_HCHO,
                   SENSOR_TEMPERATURE, SENSOR_HUMIDITY]

SENSOR_MAP = {
    SENSOR_PM25: ('μg/m³', 'blur'),
    SENSOR_HCHO: ('mg/m³', 'biohazard'),
    SENSOR_TEMPERATURE: (TEMP_CELSIUS, 'thermometer'),
    SENSOR_HUMIDITY: ('%', 'water-percent')
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): vol.Any(cv.string, list),
    vol.Optional(CONF_MAC, default=['']):
        vol.All(cv.ensure_list, vol.Length(min=1)),
    vol.Optional(CONF_SENSORS, default=DEFAULT_SENSORS):
        vol.All(cv.ensure_list, vol.Length(min=1), [vol.In(SENSOR_MAP)]),
})

# True: Thread mode, False: HomeAssistant update/poll mode
AIRCAT_SENSOR_THREAD_MODE = True


def setup_platform(hass, conf, add_devices, discovery_info=None):
    """Set up the AirCat sensor."""
    name = conf[CONF_NAME]
    macs = conf[CONF_MAC]
    sensors = conf[CONF_SENSORS]

    aircat = AirCatData()
    count = len(macs)

    if AIRCAT_SENSOR_THREAD_MODE:
        import threading
        threading.Thread(target=aircat.loop).start()
    else:
        AirCatSensor.times = 0
        AirCatSensor.interval = len(sensors) * count

    devices = []
    for index in range(count):
        device_name = name[index] if isinstance(name, list) else name + str(index + 1)
        for sensor_index in range(len(sensors)):
            sensor_type = sensors[sensor_index]
            sensor_name = device_name[sensor_index] if isinstance(device_name, list) else device_name + ' ' + sensor_type
            devices.append(AirCatSensor(aircat, sensor_name, macs[index], sensor_type))

    add_devices(devices)


class AirCatSensor(Entity):
    """Implementation of a AirCat sensor."""

    def __init__(self, aircat, name, mac, sensor_type):
        """Initialize the AirCat sensor."""
        unit, icon = SENSOR_MAP[sensor_type]
        self._name = name
        self._mac = mac
        self._sensor_type = sensor_type
        self._unit = unit
        self._icon = 'mdi:' + icon
        self._aircat = aircat

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._sensor_type

    @property
    def available(self):
        """Return if the sensor data are available."""
        return self.attributes is not None

    @property
    def state(self):
        """Return the state of the device."""
        attributes = self.attributes
        if attributes is None:
            return None
        state = attributes['value' if self._sensor_type == SENSOR_PM25 else self._sensor_type]
        if self._sensor_type == SENSOR_PM25:
            return state
        elif self._sensor_type == SENSOR_HCHO:
            return float(state) / 1000
        else:
            return round(float(state), 1)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self.attributes if self._sensor_type == SENSOR_PM25 else None

    @property
    def attributes(self):
        """Return the attributes of the device."""
        if self._mac:
            return self._aircat.devs.get(self._mac)
        for mac in self._aircat.devs:
            return self._aircat.devs[mac]
        return None

    def update(self):
        """Update state."""
        if AIRCAT_SENSOR_THREAD_MODE:
            #_LOGGER.debug("Running in thread mode")
            return

        if AirCatSensor.times % AirCatSensor.interval == 0:
            # _LOGGER.debug("Begin update %d: %s %s", AirCatSensor.times,
            #    self._mac, self._sensor_type)
            self._aircat.update()
            # _LOGGER.debug("Ended update %d: %s %s", AirCatSensor.times,
            #    self._mac, self._sensor_type)
        AirCatSensor.times += 1

    def shutdown(self, event):
        """Signal shutdown."""
        # _LOGGER.debug('Shutdown')
        self._aircat.shutdown()
