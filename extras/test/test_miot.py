#!/usr/bin/env python3

from miio.miot_device import MiotDevice

device = MiotDevice(
{
    'power': {'siid': 2, 'piid': 1}, 
    'power2': {'siid': 5, 'piid': 10}, 
    'power3': {'siid': 2, 'piid': 3}, 
    'power4': {'siid': 2, 'piid': 4}, 
    'power5': {'siid': 2, 'piid': 5}, 
    'power6': {'siid': 2, 'piid': 6}, 
    'power7': {'siid': 2, 'piid': 7}, 
    'power8': {'siid': 2, 'piid': 8}, 
    'power9': {'siid': 2, 'piid': 10}, 
    'powerA': {'siid': 2, 'piid': 11}, 
    'powerB': {'siid': 5, 'piid': 2}, 
    'powerC': {'siid': 6, 'piid': 1}, 
    'powerD': {'siid': 5, 'piid': 4}, 
    'powerE': {'siid': 5, 'piid': 5},
}, '192.168.1.28', '6dd1ec1c895a61d1b994b4a6242efe56')

print('%s' % device.get_properties_for_mapping())
