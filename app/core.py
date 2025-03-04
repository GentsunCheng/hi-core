from modules.devices import device_classes

# 遍历并实例化所有 `Device` 设备
for name, DeviceClass in device_classes.items():
    device = DeviceClass()  # 实例化
    print(f"Initializing {name}...")
