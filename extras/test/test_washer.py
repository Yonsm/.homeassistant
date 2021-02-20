#!/usr/bin/env python3

from miio.device import Device

device = Device('Washer', '1f63e0afaa20d062223b24c98eca7c11')
info = device.info()
print('%s' % info)

device.send("set_wash_program", ['goldenwash'])

#device.send("set_wash_action", [0]) # 0=Pause/1=Wash/2=PowerOff
#device.send("SetDryMode", ['17922']) # 0
# print('set_appoint_time=0: %s' % device.send("set_appoint_time", [0]))
# print('set_appoint_time: %s' % device.send("set_appoint_time", [20]))

properties = [
            "program", # dry=黄金烘/weak_dry=低温烘/refresh=空气洗/wool=羊毛/down=羽绒服/drumclean=筒清洁/goldenwash=黄金洗/super_quick=超快洗/cottons=棉织物/antibacterial=除菌洗/rinse_spin=漂+脱/spin单脱水/quick=快洗/shirt=衬衣/jeans=牛仔/underwears=内衣
            "wash_process", # 0=Idle/1=Prepare/1=Pause/.../7=Stop/预约等待=0
            "wash_status", # 1=Idle/1=Prepare/0=Pause/1=Stop/预约等待=1
            "water_temp",
            "rinse_status",
            "spin_level",
            "remain_time",
            "appoint_time",
            "be_status",
            "run_status",
            "DryMode", # 0=NA/33282=智能/半小时=7681/15361=一小时/30721=两小时
            "child_lock"
        ]

# Limited to a single property per request
values = {}
for prop in properties:
    values[prop] = device.send("get_prop", [prop])

print('%s' % values)
