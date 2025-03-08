import os
import time
import json
import threading
from flask import Flask, request
from flask_restful import Api, Resource, reqparse, abort
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.api import api
from modules.devices import device_classes

# 设备管理器，用于初始化设备、周期性发送指令等
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
        self._th1 = threading.Thread(target=self.run)
        self._th1.start()

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
        """ 进入主循环，定期发送指令 """
        while True:
            time.sleep(1)
            self.cmd_json_data["devices"] = []
            for device_id, device in self.device_instances.items():
                # 当设备有动作且已初始化完成时，将其数据加入指令队列
                if device.action and self.init_time_dict.get(device_id) is None:
                    self.cmd_json_data["devices"].append(device.data)
                    device.action = False
            if self.debug_value == 'True':
                print(json.dumps(self.cmd_json_data, indent=4))
            if self.cmd_json_data["devices"]:
                self.send_commands(self.cmd_json_data)

    def send_commands(self, cmd_json_data):
        """ 发送设备指令并处理响应 """
        data = self.hi_api.oprate(json.dumps(cmd_json_data))
        try:
            response = json.loads(data)
        except json.JSONDecodeError:
            print("无法解析JSON数据")
            return
        for item in response["actions"]:
            device = self.device_instances.get(item["id"])
            if device:
                # 更新设备状态
                device.data["param"]["present"] = item["param"]
                self.all_json_data["devices"][item["id"]]["param"]["present"] = item["param"]
                self.hi_api.set_data(json.dumps(self.all_json_data))

# 定义RESTful API资源

# 用于获取所有设备信息
class DevicesList(Resource):
    def __init__(self, **kwargs):
        self.device_manager = kwargs['device_manager']

    def get(self):
        """
        返回所有设备的实时状态和可调参数
        返回示例：
        {
            "devices": [ ... ]
        }
        """
        return {"devices": self.device_manager.all_json_data["devices"]}, 200

# 用于获取单个设备信息和调整设备参数
class DeviceControl(Resource):
    def __init__(self, **kwargs):
        self.device_manager = kwargs['device_manager']

    def get(self, device_id):
        """ 获取指定设备的详细信息 """
        device = next((d for d in self.device_manager.all_json_data["devices"] if d["id"] == device_id), None)
        if device is None:
            abort(404, message=f"Device with id {device_id} not found")
        return device, 200

    def put(self, device_id):
        """
        修改指定设备的参数
        请求示例：
        {
          "param": {
            "status": "off",
            "lightness": 3
          }
        }
        系统将构造如下命令数据，并调用send_commands：
        {
          "actions": [
            {
              "id": device_id,
              "param": {
                "status": "off",
                "lightness": 3
              }
            }
          ]
        }
        """
        json_data = request.get_json(force=True)
        if "param" not in json_data:
            return {"message": "缺少 'param' 参数"}, 400

        command_data = {
            "actions": [
                {
                    "id": device_id,
                    "param": json_data["param"]
                }
            ]
        }
        # 调用DeviceManager的send_commands方法发送指令
        self.device_manager.send_commands(command_data)
        # 返回更新后的设备状态
        updated_device = next((d for d in self.device_manager.all_json_data["devices"] if d["id"] == device_id), None)
        if updated_device is None:
            abort(404, message=f"Device with id {device_id} not found")
        return updated_device, 200

# RESTful API封装类
class restful_api:
    def __init__(self, device_manager):
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.device_manager = device_manager
        self.setup_routes()

    def setup_routes(self):
        self.api.add_resource(DevicesList, '/devices', resource_class_kwargs={'device_manager': self.device_manager})
        self.api.add_resource(DeviceControl, '/devices/<int:device_id>', resource_class_kwargs={'device_manager': self.device_manager})

if __name__ == "__main__":
    # 启动设备管理器（内部包含设备初始化及周期性发送指令的线程）
    manager = DeviceManager()
    # 启动 RESTful API 服务
    api_server = restful_api(manager)
    api_server.app.run(host="0.0.0.0", port=5000, debug=True)
