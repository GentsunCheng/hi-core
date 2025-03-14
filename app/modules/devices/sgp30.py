import os
import time
import threading
import smbus2

debug_value = os.environ.get('DEBUG')

if debug_value == 'True':
    import random
else:
    class SGP30:
        def __init__(self, i2c_bus=3, addr=0x58):
            self.addr = addr
            self.i2c = smbus2.SMBus(i2c_bus)  # 使用 smbus2 库来创建 I2C 对象
            self.init_done = threading.Event()
            self.init_command = [0x20, 0x03]  # 初始化命令
            self.read_command = [0x20, 0x08]  # 读取 CO2 和 TVOC 数据的命令
            self.i2c.write_i2c_block_data(self.addr, self.init_command[0], self.init_command[1:])

        def read(self):
            try:
                # 发送读取数据命令
                self.i2c.write_i2c_block_data(self.addr, self.read_command[0], self.read_command[1:])
                time.sleep(0.1)  # 等待数据准备

                # 读取 6 字节的数据
                data = self.i2c.read_i2c_block_data(self.addr, 0x00, 6)

                # 解析 CO2 和 TVOC 数据
                co2 = (data[0] << 8) | data[1]  # CO2 数据
                tvoc = (data[3] << 8) | data[4]  # TVOC 数据

                return co2, tvoc
            except Exception as e:
                print(f"读取 SGP30 数据失败: {e}")
                return None, None


class Device():
    def __init__(self):
        self.data = {
            "name": "sgp30",
            "id": None,
            "type": "sensor",
            "readme": "Its a sensor to measure CO2 and TVOC",
            "param": {
                "present": {
                    "co2": {
                        "content": 400,
                        "measure": "ppm"
                    },
                    "tvoc": {
                        "content": 0,
                        "measure": "ppb"
                    }
                }
            }
        }
        self.uuid = "7031be97-7758-4eec-9f77-06a83112554f"
        self.action = False
        self.init_time = 15 if debug_value == 'False' or debug_value is None else 0
        if debug_value == 'False' or debug_value is None:
            self.sgp30 = SGP30()
        self.thread = threading.Thread(target=self.__run__)
        self.thread.start()
        

    def __run__(self):
        # 初始化记录上一次状态及上次触发报警时间
        # 这里定义状态分为三档："normal" 正常，"abnormal1" 异常一级，"abnormal2" 异常二级
        prev_co2_level = "normal"
        prev_tvoc_level = "normal"
        last_trigger_time_co2 = time.time()
        last_trigger_time_tvoc = time.time()

        while True:
            try:
                if debug_value == 'True':
                    co2, tvoc = random.randint(380,500), random.randint(0,10)
                else:
                    co2, tvoc = self.sgp30.read()
                self.data["param"]["present"]["co2"]["content"] = co2
                self.data["param"]["present"]["tvoc"]["content"] = tvoc
                current_time = time.time()

                if co2 is None or tvoc is None:
                    time.sleep(1)
                    continue

                # 根据预设阈值判断 CO2 状态（可根据实际情况调整）
                if co2 < 1000:
                    current_co2_level = "normal"
                elif co2 < 1500:
                    current_co2_level = "abnormal1"
                else:
                    current_co2_level = "abnormal2"

                # 根据预设阈值判断 TVOC 状态（可根据实际情况调整）
                if tvoc < 500:
                    current_tvoc_level = "normal"
                elif tvoc < 1000:
                    current_tvoc_level = "abnormal1"
                else:
                    current_tvoc_level = "abnormal2"

                # ----- CO2 逻辑 -----
                # 情况1：从正常进入异常
                if prev_co2_level == "normal" and current_co2_level != "normal":
                    self.action = True
                    last_trigger_time_co2 = current_time
                # 情况2：在异常状态下进一步升高一级（例如从 abnormal1 升至 abnormal2）
                elif prev_co2_level == "abnormal1" and current_co2_level == "abnormal2":
                    self.action = True
                    last_trigger_time_co2 = current_time
                # 情况3：持续异常，每隔一分钟触发一次
                elif current_co2_level != "normal" and (current_time - last_trigger_time_co2 >= 60):
                    self.action = True
                    last_trigger_time_co2 = current_time

                # ----- TVOC 逻辑 -----
                if prev_tvoc_level == "normal" and current_tvoc_level != "normal":
                    self.action = True
                    last_trigger_time_tvoc = current_time
                elif prev_tvoc_level == "abnormal1" and current_tvoc_level == "abnormal2":
                    self.action = True
                    last_trigger_time_tvoc = current_time
                elif current_tvoc_level != "normal" and (current_time - last_trigger_time_tvoc >= 60):
                    self.action = True
                    last_trigger_time_tvoc = current_time

                # 更新上一次的状态
                prev_co2_level = current_co2_level
                prev_tvoc_level = current_tvoc_level

                time.sleep(1)
            except KeyboardInterrupt:
                break
