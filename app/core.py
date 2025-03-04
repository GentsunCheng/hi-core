import os
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.api import api
from modules.devices import device_classes

debug_value = os.environ.get('DEBUG')

# 构造初始化数据
all_json_data = {
    "action": "init",
    "init_param": {
        "Designation": "Madis",
        "custom": "No need to be energy efficient, but you need to be comfortable, no light when you sleep, and absolute silence."
    },
    "devices": []
}

# 存储设备实例和ID
device_instances = {}  # 用字典存储，key 为设备名称
i = 0
init_time_dict = {}

# 遍历并实例化所有设备，并保存到 device_instances 中
for name, DeviceClass in device_classes.items():
    device = DeviceClass()  # 实例化
    print(f"Initializing {device.data["name"]}...")
    # 假设 device.data 是存储设备信息的字典
    device.data["id"] = i
    i += 1
    all_json_data["devices"].append(device.data)
    # 假设 device.init_time 表示初始化需要等待的时间
    if device.init_time != 0:
        init_time_dict[device.data["id"]] = device.init_time
    device_instances[device.data["id"]] = device

del i

if debug_value == 'True':
    print(json.dumps(all_json_data, indent=4))

# 初始化命令数据结构
cmd_json_data = {
    "action": "cmd",
    "devices": []
}

# 初始化 hi_api 
hi_api = api.HI_api()
hi_api.set_data(json.dumps(all_json_data))

# 等待传感器初始化
def init_device(device_id, wait_time):
    """
    模拟传感器初始化，等待指定时间后返回设备 id
    """
    time.sleep(wait_time)
    print(f"设备 {device_id} 初始化完成")
    return device_id

# 使用线程池同时初始化所有传感器
with ThreadPoolExecutor(max_workers=len(init_time_dict)) as executor:
    future_to_device = {
        executor.submit(init_device, device_id, wait_time): device_id
        for device_id, wait_time in init_time_dict.items()
    }
    # 当有任务完成时，立即删除对应的标志
    for future in as_completed(future_to_device):
        device_id = future_to_device[future]
        try:
            result = future.result()
            # 完成一个就删除对应的标志
            init_time_dict.pop(result, None)
            print(f"已删除 {result} 的初始化标志, 剩余标志：{init_time_dict}")
        except Exception as exc:
            print(f"设备 {device_id} 初始化时发生异常: {exc}")

while True:
    # 每隔一段时间循环一次
    time.sleep(1)
    # 清空之前的命令数据
    cmd_json_data["devices"] = []
    
    # 遍历已实例化的设备
    for name, device in device_instances.items():
        if device.action and init_time_dict["id"] is None:
            cmd_json_data["devices"].append(device.data)
            # 修改状态为 False，确保下次不重复发送同样的命令
            device.action = False
            
    if debug_value == 'True':
        print(json.dumps(cmd_json_data, indent=4))

    # 如果有命令数据则发送
    if cmd_json_data["devices"]:
        data = hi_api.oprate(json.dumps(cmd_json_data))
        try:
            response = json.loads(data)
        except json.JSONDecodeError:
            print("无法解析JSON数据")
            continue
        for item in response["actions"]:
            device_instances[item["id"]]["param"]["present"] = item["param"]
            all_json_data["devices"][item["id"]]["param"]["present"] = item["param"]
            hi_api.set_data(json.dumps(all_json_data))

