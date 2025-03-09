import os
import time
import threading
from periphery import I2C

debug_value = os.environ.get('DEBUG')

if debug_value == 'True':
    import random
else:
    class SGP30:
        INIT_COMMAND = [0x20, 0x03]
        READ_COMMAND = [0x20, 0x08]
        
        def __init__(self, i2c_bus="/dev/i2c-0", addr=0x58):
            self.addr = addr
            self.i2c = I2C(i2c_bus)
            self.init_done = threading.Event()

            self._send_init_command()
            
            self.init_thread = threading.Thread(target=self._wait_for_init, daemon=True)
            self.init_thread.start()

        def _send_init_command(self):
            """发送初始化命令到 SGP30"""
            try:
                self.i2c.transfer(self.addr, [self.i2c.Message(self.INIT_COMMAND)])
            except Exception as e:
                print(f"SGP30 初始化失败: {e}")

        def _wait_for_init(self):
            """等待 15 秒后标记初始化完成"""
            print("请等待 15 秒以完成 SGP30 初始化...")
            time.sleep(15)
            self.init_done.set()

        def read(self):
            """获取 SGP30 传感器数据（CO2 和 TVOC），确保初始化完成"""
            if not self.init_done.wait(timeout=16):
                raise TimeoutError("SGP30 初始化超时")

            try:
                self.i2c.transfer(self.addr, [self.i2c.Message(self.READ_COMMAND)])
                msgs = [self.i2c.Message([0x00, 0x00, 0x00, 0x00], read=True)]
                self.i2c.transfer(self.addr, msgs)

                co2 = (msgs[0].data[0] << 8) | msgs[0].data[1]
                tvoc = (msgs[0].data[2] << 8) | msgs[0].data[3]
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
        self.thread = threading.Thread(target=self.__read__)
        self.thread.start()
        

    def __read__(self):
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
