import os
import time
import json
import toml
import sqlite3
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.api import Hi_AI
from modules.devices import device_classes

from flask import Flask, request, jsonify

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

with open(os.getcwd() + "/source/config.toml", "r", encoding="utf-8") as f:
            config = toml.load(f)
            https = False
            if config["http"]["host"] != "":
                host = config["http"]["host"]
            if config["http"]["port"] != "":
                port = int(config["http"]["port"])
            if config["http"]["https"]:
                cert = os.getcwd() + "/source/fullchain.pem"
                key = os.getcwd() + "/source/privkey.pem"
                if os.path.exists(cert) and os.path.exists(key):
                    https = True
                

app = Flask(__name__)

class DeviceManager:
    def __init__(self):
        self.debug_value = os.environ.get('DEBUG')
        self.all_device_config = {
            "status": "init",
            "init_param": {
                "designation": "Madis",
                "username": "orii",
                "custom": "No need to be energy efficient, but you need to be comfortable, no light when you sleep, and absolute silence."
            },
            "devices": []
        }
        self.device_instances = {}
        self.init_time_dict = {}
        self.sys_param = {}
        self.hi_ai = Hi_AI.HIAI_auto()
        self.trig_device_config = {"action": "trigger", "devices": []}
        self._db_file = os.getcwd() + "/source/data.db"
        self._writting_db = False
        self.uid ="10001"
        self._init_db()
        self._initialize_devices()
        self._start_device_initialization()

    def _init_db(self, force=False):
        self._writting_db = True
        conn = sqlite3.connect(self._db_file)
        cursor = conn.cursor()
        if force:
            cursor.execute("DROP TABLE IF EXISTS param")
            conn.commit()
            cursor.execute("DROP TABLE IF EXISTS userinfo")
            conn.commit()
        cursor.execute("CREATE TABLE IF NOT EXISTS param (id TEXT PRIMARY KEY, param BLOB)")
        conn.commit()
        cursor.execute("CREATE TABLE IF NOT EXISTS userinfo (id TEXT PRIMARY KEY, param BLOB)")
        conn.commit()
        cursor.close()
        conn.close()
        self._writting_db = False

    def _read_param_from_db(self, db, id, timeout=5):
        for i in range(timeout * 2):
            if self._writting_db:
                time.sleep(0.5)
            else:
                break
            if i == timeout * 2 - 1:
                return None
            
        self._writting_db = True
        conn = sqlite3.connect(self._db_file)
        cursor = conn.cursor()
        query = f"SELECT param FROM {db} WHERE id=?"
        cursor.execute(query, (id,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        self._writting_db = False
        if result:
            return json.loads(result[0][0].decode("utf-8"))
        else:
            return None

    def _write_param_to_db(self, db, id, value, timeout=5):
        for i in range(timeout * 2):
            if self._writting_db:
                time.sleep(0.5)
            else:
                break
            if i == timeout * 2 - 1:
                return "Failure"
        self._writting_db = True
        conn = sqlite3.connect(self._db_file)
        cursor = conn.cursor()
        query = f"INSERT INTO {db} (id, param) VALUES (?, ?)"
        cursor.execute(query, (id, json.dumps(value).encode("utf-8")))
        conn.commit()
        cursor.close()
        conn.close()
        self._writting_db = False

    def _update_param_in_db(self, db, id, value, timeout=5):
        for i in range(timeout * 2):
            if self._writting_db:
                time.sleep(0.5)
            else:
                break
            if i == timeout * 2 - 1:
                return "Failure"
        self._writting_db = True
        conn = sqlite3.connect(self._db_file)
        cursor = conn.cursor()
        query = f"UPDATE {db} SET param=? WHERE id=?"
        cursor.execute(query, (json.dumps(value).encode("utf-8"), id))
        conn.commit()
        cursor.close()
        conn.close()
        self._writting_db = False

    def _compare_keys(self, dict1, dict2):
        if set(dict1.keys()) != set(dict2.keys()):
            return False
        for key in dict1:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                if not self._compare_keys(dict1[key], dict2[key]):
                    return False
        return True

    def _initialize_devices(self):
        """ 遍历设备类并进行初始化 """
        userinfo = self._read_param_from_db(db="userinfo", id=self.uid, timeout=5)
        if userinfo:
            self.all_device_config["init_param"] = userinfo
        else:
            self._write_param_to_db(db="userinfo", id=self.uid, value=self.all_device_config["init_param"], timeout=5)
        i = 0
        for name, DeviceClass in device_classes.items():
            try:
                device = DeviceClass()
                print(f"Initializing {device.data['name']}...")
                
                if hasattr(device, "seed"):
                    param = self._read_param_from_db(db="param", id=device.seed)
                    if param:
                        device.data["param"]["present"] = param
                    else:
                        self._write_param_to_db(db="param", id=device.seed, value=device.data["param"]["present"])
                    device.unlock()
                
                device.data["id"] = i
                i += 1
                self.all_device_config["devices"].append(device.data)
                
                if device.init_time != 0:
                    self.init_time_dict[device.data["id"]] = device.init_time
                
                self.device_instances[device.data["id"]] = device
                
                self.sys_param[device.data["id"]] = device.sys_param
            
            except Exception as e:
                print(f"Failed to initialize {name}: {e}")
                continue
        
        self.hi_ai.set_data(json.dumps(self.all_device_config))
        
        if self.debug_value == 'True':
            print(json.dumps(self.all_device_config, indent=4))

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

    def set_userinfo(self, data):
        if self._compare_keys(self.all_device_config["init_param"], json.loads(data)):
            self.all_device_config["init_param"] = json.loads(data)
            self._update_param_in_db(db="userinfo", id=self.uid, value=json.loads(data), timeout=5)


    def run(self):
        """ 进入主循环，定期发送命令 """
        duration = 0
        while True:
            duration += 1
            time.sleep(1)
            if duration >= 60:
                duration = 0
                for i in range(len(self.device_instances)):
                    self.all_device_config["devices"][i] = self.device_instances[i].data
            self.trig_device_config["devices"] = []
            for device_id, device in self.device_instances.items():
                if device.trigger and self.init_time_dict.get(device_id) is None:
                    self.trig_device_config["devices"].append(device.data)
                    device.trigger = False
            if self.trig_device_config["devices"]:
                print(json.dumps(self.trig_device_config, indent=4))
                logging.info(json.dumps(self.trig_device_config, indent=4))
                data = self.hi_ai.oprate(json.dumps(self.trig_device_config))
                print(data)
                self.cmd(data)
                logging.info(data)

    def cmd(self, data):
        try:
            data_decode = json.loads(data)
            logging.info(data_decode)
        except json.JSONDecodeError:
            logging.error("无法解析 JSON 数据")
            return
        if not "actions" in data_decode:
            return
        for item in data_decode["actions"]:
            if self.device_instances[item["id"]]:
                if self._compare_keys(self.device_instances[item["id"]].data["param"]["present"], item["param"]):
                    self.device_instances[item["id"]].data["param"]["present"] = item["param"]
                else:
                    continue
                if self._compare_keys(self.all_device_config["devices"][item["id"]]["param"]["present"], item["param"]):
                    self.all_device_config["devices"][item["id"]]["param"]["present"] = item["param"]
                else:
                    continue
                self.hi_ai.set_data(json.dumps(self.all_device_config))
                if hasattr(self.device_instances[item["id"]], "seed"):
                    self._update_param_in_db(db="param", id=self.device_instances[item["id"]].seed, value=item["param"])



# 实例化设备管理器
manager = DeviceManager()

app = Flask(__name__)

# 单独启动设备管理器的 run 方法，避免阻塞 API 主线程
def run_manager():
    manager.run()

SECRET_API_KEY = os.environ.get('SECRET_API_KEY')
with open(os.getcwd() + "/source/config.toml", "r", encoding="utf-8") as f:
    config = toml.load(f)
    if config["core"]["secret_api_key"] != "":
        SECRET_API_KEY = config["core"]["secret_api_key"]

# 添加密钥认证检查，在每次请求前验证密钥
@app.before_request
def authenticate():
    # 从请求头中获取密钥，约定使用 'X-API-Key' 作为密钥字段
    api_key = request.headers.get('X-API-Key')
    if api_key != SECRET_API_KEY:
        return jsonify({"error": "Unlawful request"}), 401

threading.Thread(target=run_manager, daemon=True).start()

# 定义一个 GET 接口，用于读取所有设备的数据
@app.route('/api/devices', methods=['GET'])
def get_devices():
    # 直接返回 DeviceManager 实例中的 all_json_data 数据
    return jsonify(manager.all_device_config)

@app.route('/api/devices/sys_param', methods=['GET'])
def get_uuid():
    return jsonify(manager.sys_param)

# 定义一个 POST 接口，用于下发控制命令
@app.route('/api/control', methods=['POST'])
def control_device():
    data = request.data.decode('utf-8')
    if not data:
        return jsonify({"error": "Unsupport request"}), 400
    # cmd 函数接收的是 JSON 字符串，所以先将接收到的 JSON 数据转换为字符串再传入
    manager.cmd(data)
    return jsonify({"status": "OK"})

@app.route('/api/userinfo', methods=['GET'])
def get_userinfo():
    return jsonify(manager.all_device_config["init_param"])

@app.route('/api/userinfo', methods=['POST'])
def set_userinfo():
    data = request.data.decode('utf-8')
    if not data:
        return jsonify({"error": "Unsupport request"}), 400
    manager.set_userinfo(data)
    return jsonify({"status": "OK"})

if __name__ == '__main__':
    if https:
        app.run(host=host, port=port, ssl_context=(cert, key))
    else:
        app.run(host=host, port=port)
        