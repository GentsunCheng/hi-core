import os
import time
import threading
from periphery import I2C

debug_value = os.environ.get('DEBUG')

if debug_value == 'False' or debug_value is None:
    class SGP30:
        def __init__(self):
            self.addr = 0x58
            self.i2c = I2C("/dev/i2c-0")
            self.stat = False

            th = threading.Thread(target=self.__wait_init__)

            msgs = [self.i2c.Message([0x20, 0x03])]
            self.i2c.transfer(self.addr, msgs)
            th.start()

        def __wait_init__(self):
            print("please wait 15s for sgp30 init")
            time.sleep(15)
            self.stat = True

        def read(self):
            """
            获取sgp30数据, 初始化至少15秒使用
            返回co2, tvoc
            :return: int, int
            """
            while not self.stat:
                time.sleep(1)
            msgs = [self.i2c.Message([0x20, 0x08])]
            self.i2c.transfer(self.addr, msgs)
            time.sleep(0.1)
            msgs = [self.i2c.Message([0x00, 0x00, 0x00, 0x00], read=True)]
            self.i2c.transfer(self.addr, msgs)
            return int(msgs[0].data[0]) << 8 | int(msgs[0].data[1]), int(msgs[0].data[2]) << 8 | int(msgs[0].data[3])
        
class Device():
    def __init__(self):
        self.name = "sgp30"
        self.type = "sensor"
        self.readme = "Its a sensor to measure CO2 and TVOC"
        self.param = {
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
        self.data = {
            "name": self.name,
            "id": None,
            "type": self.type,
            "readme": self.readme,
            "param": self.param
        }
        self.action = False
        self.init_time = 15
        self.thread = threading.Thread(target=self.__read__)
        if debug_value == 'False' or debug_value is None:
            self.sgp30 = SGP30()

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
                    co2, tvoc = 400, 0
                else:
                    co2, tvoc = self.sgp30.read()
                self.param["present"]["co2"]["content"] = co2
                self.param["present"]["tvoc"]["content"] = tvoc
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
