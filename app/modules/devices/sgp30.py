import time
import threading
from periphery import I2C
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
        self.sgp30 = SGP30()