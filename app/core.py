import os
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.api import api
from modules.devices import device_classes

class DeviceManager:
    def __init__(self):
        self.debug_value = os.environ.get('DEBUG')
        self.all_json_data = {
            "action": "init",
            "init_param": {
                "Designation": "Madis",
                "custom": "No need to be energy efficient, but you need to be comfortable, no light when you sleep, and absolute silence."
            },
            "devices": []
        }
        self.device_instances = {}
        self.init_time_dict = {}
        self.hi_api = api.HI_api()
        self.cmd_json_data = {"action": "cmd", "devices": []}
        self._initialize_devices()
        self._start_device_initialization()

    def _initialize_devices(self):
        """ 遍历设备类并进行初始化 """
        i = 0
        for name, DeviceClass in device_classes.items():
            device = DeviceClass()
            print(f"Initializing {device.data['name']}...")
            device.data["id"] = i
            i += 1
            self.all_json_data["devices"].append(device.data)
            if device.init_time != 0:
                self.init_time_dict[device.data["id"]] = device.init_time
            self.device_instances[device.data["id"]] = device
        self.hi_api.set_data(json.dumps(self.all_json_data))
        if self.debug_value == 'True':
            print(json.dumps(self.all_json_data, indent=4))

    def _start_device_initialization(self):
        """ 使用线程池初始化设备 """
        def init_device(device_id, wait_time):
            time.sleep(wait_time)
            print(f"设备 {device_id} 初始化完成")
            return device_id

        if len(self.init_time_dict):
            with ThreadPoolExecutor(max_workers=len(self.init_time_dict)) as executor:
                future_to_device = {
                    executor.submit(init_device, device_id, wait_time): device_id
                    for device_id, wait_time in self.init_time_dict.items()
                }
                for future in as_completed(future_to_device):
                    device_id = future_to_device[future]
                    try:
                        result = future.result()
                        self.init_time_dict.pop(result, None)
                        print(f"已删除 {result} 的初始化标志, 剩余标志：{self.init_time_dict}")
                    except Exception as exc:
                        print(f"设备 {device_id} 初始化时发生异常: {exc}")

    def run(self):
        """ 进入主循环，定期发送命令 """
        while True:
            time.sleep(1)
            self.cmd_json_data["devices"] = []
            for device_id, device in self.device_instances.items():
                if device.action and self.init_time_dict.get(device_id) is None:
                    self.cmd_json_data["devices"].append(device.data)
                    device.action = False
            if self.debug_value == 'True':
                print(json.dumps(self.cmd_json_data, indent=4))
            if self.cmd_json_data["devices"]:
                data = self.hi_api.oprate(json.dumps(self.cmd_json_data))
                try:
                    response = json.loads(data)
                except json.JSONDecodeError:
                    print("无法解析JSON数据")
                    continue
                if "actions" in response:
                    self.cmd(response)

    def cmd(self, data):
        data_decode = json.loads(data)
        for item in data_decode["actions"]:
            if self.device_instances[item["id"]]:
                self.device_instances[item["id"]].data["param"]["present"] = item["param"]
                self.all_json_data["devices"][item["id"]]["param"]["present"] = item["param"]
                self.hi_api.set_data(json.dumps(self.all_json_data))


if __name__ == "__main__":
    manager = DeviceManager()
    manager.run()
