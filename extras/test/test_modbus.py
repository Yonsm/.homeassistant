#!/usr/bin/env python3

import struct
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.transaction import ModbusRtuFramer as ModbusFramer

# import socket
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.settimeout(5)
# s.connect(('ModBus', 8899))
# s.sendall(b'\x55\xAA\x55\x00\x25\x80\x03\xA8') # For USR initialize
# s.close()

ATTR_MAP = {
    'temperature': {'registers': [3, 6, 9, 12], 'register_type': 'input'},
    'target_temp': {'registers': [4, 8, 12, 16]},
    'operation': {'registers': [5, 9, 13, 17]},
    'fan_mode': {'registers': [6, 10, 14, 18]},
    'state_is_on': {'registers': [1, 2, 3, 4], 'register_type': 'coil'}
}

client = ModbusClient(host='ModBus', port=8899, framer=ModbusFramer)
kwargs = {'unit': 1}

for key in ATTR_MAP:
    dict = ATTR_MAP[key]
    print("%s:\t" % key, end='')
    for register in dict['registers']:
        register_type = dict.get('register_type')
        if register_type == 'coil':
            result = client.read_coils(register, 1, **kwargs)
            value = bool(result.bits[0])
        else:
            if register_type == 'input':
                result = client.read_input_registers(register, 1, **kwargs)
            else:
                result = client.read_holding_registers(register, 1, **kwargs)
            byte_string = b''.join([x.to_bytes(2, byteorder='big')
                                    for x in result.registers])
            value = struct.unpack('>H', byte_string)[0]
        print("%s\t" % value, end='')
    print("")
