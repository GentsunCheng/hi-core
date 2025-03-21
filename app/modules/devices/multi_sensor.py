import os
import time
import threading
import smbus2

debug_value = os.environ.get('DEBUG')

if debug_value == 'True':
    import random
else:
    class Multi_Sensor:
        def __init__(self, i2c_bus=3):
            self._i2c = smbus2.SMBus(i2c_bus)  # 使用 smbus2 库来创建 I2C 对象
            self._sgp30_addr = 0x58
            self._bh1750_addr = 0x23
            self._aht10_addr = 0x38
            self._bh1750_one_time_high_res_mode = 0x20
            self._sgp30_init_command = [0x20, 0x03]  # 初始化命令
            self._sgp30_read_command = [0x20, 0x08]  # 读取 CO2 和 TVOC 数据的命令
            self._i2c.write_i2c_block_data(self._sgp30_addr, self._sgp30_init_command[0], self._sgp30_init_command[1:])

        def bh1750_read(self):
            try:
                # 发送读取数据命令
                self._i2c.write_byte(self._bh1750_addr, self._bh1750_one_time_high_res_mode)
                time.sleep(0.2)  # 等待数据准备
                # 读取 2 字节的数据
                data = self._i2c.read_i2c_block_data(self._bh1750_addr, 0x00, 2)
                # 解析光照度数据
                light = (data[0] << 8) | data[1]
                light /= 1.2
                return "{:.2f}".format(light)
            except Exception as e:
                print(f"读取 BH1750 数据失败: {e}")
                return None
            
        def aht10_read(self):
            try:
                # 发送读取数据命令
                self._i2c.write_i2c_block_data(self._aht10_addr, 0xAC, [0x33, 0x00])
                time.sleep(0.1)  # 等待数据准备

                # 读取 6 字节的数据
                data = self._i2c.read_i2c_block_data(self._aht10_addr, 0x00, 6)

                # 解析温度和湿度数据
                temperature = (((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]) * 200.0 / 1048576.0 - 50
                humidity = ((data[1] << 12) | (data[2] << 4) | (data[3] >> 4)) * 100.0 / 1048576.0

                return "{:.2f}".format(temperature), "{:.2f}".format(humidity)
            except Exception as e:
                print(f"读取 AHT10 数据失败: {e}")
                return None
            
        def sgp30_read(self):
            try:
                # 发送读取数据命令
                self._i2c.write_i2c_block_data(self._sgp30_addr, self._sgp30_read_command[0], self._sgp30_read_command[1:])
                time.sleep(0.1)  # 等待数据准备

                # 读取 6 字节的数据
                data = self._i2c.read_i2c_block_data(self._sgp30_addr, 0x00, 6)

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
            "name": "multi_sensor",
            "id": None,
            "type": "sensor",
            "readme": "Its a multi sensor to measure CO2, TVOC, Light, Temperature and Humidity",
            "param": {
                "present": {
                    "co2": {
                        "content": 400,
                        "measure": "ppm"
                    },
                    "tvoc": {
                        "content": 0,
                        "measure": "ppb"
                    },
                    "light": {
                        "content": 0,
                        "measure": "lx"
                    },
                    "temperature": {
                        "content": 25,
                        "measure": "°C"
                    },
                    "humidity": {
                        "content": 70,
                        "measure": "%"
                    }
                }
            }
        }
        self.sys_param = {
            "show": True,
            "uuid": "7031be97-7758-4eec-9f77-06a83112554f"
        }
        self.trigger = False
        self.init_time = 0
        if debug_value == 'False' or debug_value is None:
            self._multi_sensor = Multi_Sensor()
        self._thread = threading.Thread(target=self.__run__, daemon=True)
        self._thread.start()
        

    def __run__(self):
        # 初始化记录上一次状态及上次触发报警时间
        # 这里定义状态分为三档："normal" 正常，"abnormal1" 异常一级，"abnormal2" 异常二级
        prev_co2_level = "normal"
        prev_tvoc_level = "normal"
        prev_temperature_level = "normal"
        prev_humidity_level = "normal"
        last_trigger_time_co2 = time.time()
        last_trigger_time_tvoc = time.time()
        last_trigger_time_temperature = time.time()
        last_trigger_time_humidity = time.time()

        while True:
            try:
                if debug_value == 'True':
                    co2, tvoc = random.randint(380,450), random.randint(0,10)
                    light = random.randint(0,1000)
                    temperature, humidity = random.randint(25,28), random.randint(60,70)
                else:
                    co2, tvoc = self._multi_sensor.sgp30_read()
                    light = float(self._multi_sensor.bh1750_read())
                    temperature, humidity = float(self._multi_sensor.aht10_read()[0]), float(self._multi_sensor.aht10_read()[1])
                self.data["param"]["present"]["co2"]["content"] = co2 if co2 is not None else 0
                self.data["param"]["present"]["tvoc"]["content"] = tvoc if tvoc is not None else 0
                self.data["param"]["present"]["light"]["content"] = light if light is not None else 0
                self.data["param"]["present"]["temperature"]["content"] = temperature if temperature is not None else 25
                self.data["param"]["present"]["humidity"]["content"] = humidity if humidity is not None else 70
                current_time = time.time()

                # 根据预设阈值判断 CO2 状态（可根据实际情况调整）
                if co2 < 800:
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

                # 根据预设阈值判断 Temperature 状态（可根据实际情况调整）
                if temperature < 18:
                    current_temperature_level = "cold" 
                elif 18 <= temperature < 30:
                    current_temperature_level = "normal"
                else:
                    current_temperature_level = "hot"

                # 根据预设阈值判断 Humidity 状态（可根据实际情况调整）
                if humidity < 50:
                    current_humidity_level = "dry"
                elif 50 <= humidity <= 80:
                    current_humidity_level = "normal"
                else:
                    current_humidity_level = "wet"

                # ----- CO2 逻辑 -----
                # 情况1：从正常进入异常
                if prev_co2_level == "normal" and current_co2_level != "normal":
                    self.trigger = True
                    last_trigger_time_co2 = current_time
                # 情况2：在异常状态下进一步升高一级（例如从 abnormal1 升至 abnormal2）
                elif prev_co2_level == "abnormal1" and current_co2_level == "abnormal2":
                    self.trigger = True
                    last_trigger_time_co2 = current_time
                # 情况3：持续异常，每隔一分钟触发一次
                elif current_co2_level != "normal" and (current_time - last_trigger_time_co2 >= 60):
                    self.trigger = True
                    last_trigger_time_co2 = current_time

                # ----- TVOC 逻辑 -----
                if prev_tvoc_level == "normal" and current_tvoc_level != "normal":
                    self.trigger = True
                    last_trigger_time_tvoc = current_time
                elif prev_tvoc_level == "abnormal1" and current_tvoc_level == "abnormal2":
                    self.trigger = True
                    last_trigger_time_tvoc = current_time
                elif current_tvoc_level != "normal" and (current_time - last_trigger_time_tvoc >= 60):
                    self.trigger = True
                    last_trigger_time_tvoc = current_time

                # ----- Temperature 逻辑 ----
                if prev_temperature_level == "normal" and current_temperature_level != "normal":
                    self.trigger = True
                    last_trigger_time_temperature = current_time
                elif current_temperature_level != "normal" and (current_time - last_trigger_time_temperature >= 60):
                    self.trigger = True
                    last_trigger_time_temperature = current_time

                # ----- Humidity 逻辑 -----
                if prev_humidity_level == "normal" and current_humidity_level != "normal":
                    self.trigger = True
                    last_trigger_time_humidity = current_time
                elif current_humidity_level != "normal" and (current_time - last_trigger_time_humidity >= 60):
                    self.trigger = True
                    last_trigger_time_humidity = current_time

                # 更新上一次的状态
                prev_co2_level = current_co2_level
                prev_tvoc_level = current_tvoc_level
                prev_temperature_level = current_temperature_level
                prev_humidity_level = current_humidity_level

                time.sleep(1)
            except KeyboardInterrupt:
                break


if __name__ == "__main__":
    multi_sensor = Multi_Sensor()
    while True:
        co2, tvoc = multi_sensor.sgp30_read()
        print(f"CO2: {co2} ppm, TVOC: {tvoc} ppb")
        time.sleep(1)
        light = multi_sensor.bh1750_read()
        print(f"光照强度: {light:.2f} lx")
        time.sleep(1)
        temp, humi = multi_sensor.aht10_read()
        print(f"温度: {temp:.2f} °C, 湿度: {humi:.2f} %")
        time.sleep(1)

    