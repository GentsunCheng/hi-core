import os
import glob
import importlib

# 发现所有设备模块
module_files = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
module_names = [os.path.basename(f)[:-3] for f in module_files if f.endswith(".py") and f != "__init__.py"]

# 存储所有设备的 `Device` 类
device_classes = {}

for module in module_names:
    try:
        mod = importlib.import_module(f"modules.devices.{module}")
    except ImportError as e:
        print(f"Error importing module {module}: {e}")
        continue

    # 获取模块中的 `Device` 类
    if hasattr(mod, "Device"):
        device_classes[module] = getattr(mod, "Device")  # 设备名 -> 设备类

# 让 `from modules.devices import *` 可用
__all__ = ["device_classes"]
