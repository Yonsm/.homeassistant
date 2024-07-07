#!/usr/bin/env python3

import struct
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import ModbusRtuFramer

HOST = '192.168.1.60'
PORT = 8899


def reset(host, port):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((host, port))
    s.sendall(b'\x55\xAA\x55\x00\x25\x80\x03\xA8')  # For USR initialize
    s.close()


ATTR_MAP = {
    'target_temp': {'registers': [4, 8, 12, 16]},
    'temperature': {'registers': [3, 6, 9, 12], 'register_type': 'input'},
    'operation': {'registers': [5, 9, 13, 17]},
    'fan_mode': {'registers': [6, 10, 14, 18]},
    'state_is_on': {'registers': [1, 2, 3, 4], 'register_type': 'coil'}
}

#reset(HOST, PORT)

client = ModbusTcpClient(host=HOST, port=PORT, framer=ModbusRtuFramer)
kwargs = {'unit': 1}
ret = client.connect()

for k, v in ATTR_MAP.items():
    print("%s:\t" % k, end='')
    for register in v['registers']:
        register_type = v.get('register_type')
        if register_type == 'coil':
            result = client.read_coils(register, 1, **kwargs)
            value = bool(result.bits[0])
        else:
            if register_type == 'input':
                result = client.read_input_registers(register, 1, **kwargs)
            else:
                result = client.read_holding_registers(register)
            if isinstance(result, Exception):
                print("Exception: %s" % result)
                continue
            byte_string = b''.join([x.to_bytes(2, byteorder='big') for x in result.registers])
            value = struct.unpack('>H', byte_string)[0]
        print("%s\t" % value, end='')
    print("")
