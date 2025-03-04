import json
from modules.api import api
from modules.devices import device_classes

hi_api = api.HI_api()


all_json_data = {
    "action": "init",
    "init_param": {
        "Designation": "Madis",
        "custom": "No need to be energy efficient, but you need to be comfortable, no light when you sleep, and absolute silence."
    },
    "devices": []
}

id = []

i = 0
# 遍历并实例化所有 `Device` 设备
for name, DeviceClass in device_classes.items():
    device = DeviceClass()  # 实例化
    print(f"Initializing {name}...")
    device.data["id"] = i
    id.append(device.data["id"])
    i += 1
    all_json_data["devices"].append(device.data)
del i

print(json.dumps(all_json_data, indent=4))
print(id)

cmd_json_data = {
    "action": "cmd",
    "devices": []
}
while True:
    for name, DeviceClass in device_classes.items():
        device = DeviceClass()
        if device.action:
            cmd_json_data["devices"].append(device.data)
            device.action = False

    if cmd_json_data["devices"]:
