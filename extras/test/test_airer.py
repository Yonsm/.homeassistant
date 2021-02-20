#!/usr/bin/env python3

from miio.device import Device

device = Device('Airer', 'fe5a1e19a1fd91ca4138646a494a6f19')
#device_info = device.info()
#device.send("set_led", [0])
#print('%s' % device_info)

for prop in ["dry","led","motor","drytime","airer_location"]:
	try:
		ret = device.send("get_prop", [prop])
	except Exception as exc:
		ret = exc
	print('%s=%s' % (prop, ret))

#device.send("set_motor", [1]) # 1-Up/0=Pause/2=Down
