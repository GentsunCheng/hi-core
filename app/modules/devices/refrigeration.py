import time
import copy
import json
import threading
from periphery import Serial


class Refrigeration:
    def __init__(self, brand, serial_port="/dev/ttyS5"):
        self._header = [0xAA, 0x55, 0x0A]
        self.brands_list = {
            "gree": 0x0BB9,
            "midea": 0x0BBA,
            "hualing": 0x0BBB,
            "little_swan": 0x0BBC,
            "hisense": 0x0BBD,
            "kelon": 0x0BBE,
            "tcl": 0x0BBF,
            "haier": 0x0BC0,
            "konka": 0x0BC1,
            "yuetu": 0x0BC2,
            "hitachi": 0x0BC3,
            "aux": 0x0BC4,
            "chigo": 0x0BC5,
            "panason": 0x0BC6,
            "daikin": 0x0BC7,
            "xiaomi": 0x0BC8,
            "samsung": 0x0BC9,
            "changhong": 0x0BCA,
            "mitsubishi": 0x0BCB,
            "longhong": 0x0BCC
        }
        self.power = {
            "off": 0,
            "on": 1,
        }
        self.fan_up_and_down = {
            "off": 0,
            "on": 1,
        }
        self.screen = {
            "off": 0,
            "on": 1,
        }
        self.fan_left_and_right = {
            "off": 0,
            "on": 1,
        }
        self.mode = {
            "auto": 0x00,
            "cool": 0x01,
            "dry": 0x02,
            "wind": 0x03,
            "heat": 0x04
        }
        self.fan_speed = {
            "auto": 0x00,
            "low": 0x01,
            "medium": 0x02,
            "high": 0x03
        }
        self.key_core = {
            "power": 0x00,
            "fan_up_and_down": 0x01,
            "fan_left_and_right": 0x02,
            "temperature_up": 0x03,
            "temperature_down": 0x04,
            "mode": 0x05,
            "fan_speed": 0x06,
            "screen": 0x07
        }
        self._serial = Serial(serial_port, 9600)
        self.brand = brand
    
    def control(self, data):
        brands_code = self.brands_list[self.brand]
        power_code = self.power[data["power"]]
        fan_up_and_down_code = self.fan_up_and_down[data["fan_up_and_down"]]
        screen_code = self.screen[data["screen"]]
        fan_left_and_right_code = self.fan_left_and_right[data["fan_left_and_right"]]
        temperature_code = data["temperature"] - 16
        code1 = power_code << 7 | fan_up_and_down_code << 6 | fan_left_and_right_code << 5 | screen_code << 4 | temperature_code
        code2 = self.mode[data["mode"]] << 4 | self.fan_speed[data["fan_speed"]]
        key_code = self.key_core[data["key_core"]]
        param_code = 0x00
        command = self._header + [0x00] + [0x00] + [brands_code >> 8, brands_code & 0xFF] + [code1, code2, 0x00, key_code, param_code]
        checksum = 0
        for byte in command:
            checksum ^= byte
        command.append(checksum)
        self._serial.write(command)
        

class Device:
    def __init__(self):
        self.data = {
            "name": "refrigeration",
            "id": None,
            "type": "refrigeration",
            "readme": "This unit is an air conditioner with adjustable modes, temperature and air speed",
            "param": {
                "present": {
                    "power": "off",
                    "fan_up_and_down": "off",
                    "screen": "off",
                    "fan_left_and_right": "off",
                    "temperature": 25,
                    "mode": "auto",
                    "fan_speed": "auto"
                },
                "selection": {
                    "power": ["__SELECT__", "off", "on"],
                    "fan_up_and_down": ["__SELECT__", "off", "on"],
                    "screen": ["__SELECT__", "off", "on"],
                    "fan_left_and_right": ["__SELECT__", "off", "on"],
                    "temperature": ["__RANGE__", 16, 30],
                    "mode": ["__SELECT__", "auto", "cool", "dry", "wind", "heat"],
                    "fan_speed": ["__SELECT__", "auto", "low", "medium", "high"]
                }
            }
        }
        self.uuid = "ece5a5ed-06cd-4f1a-a607-e8a23f976cd6"
        self.trigger = False
        self.init_time = 0
        self.seed = "fzt8so0xx3hv1ib87zluixu8td7koktk"
        self._lock = True
        self._refrigeration = Refrigeration(brand="gree")
        self._thread = threading.Thread(target=self.__run__, daemon=True)
        self._thread.start()

    def unlock(self):
        self._lock = False

    def __run__(self):
        while self._lock:
            time.sleep(1)
            data = copy.deepcopy(self.data)
            try:
                while True:
                    if json.dumps(self.data["param"]["present"], sort_keys=True) != json.dumps(data["param"]["present"], sort_keys=True):
                        self._refrigeration.control(self.data["param"]["present"])
                        data = copy.deepcopy(self.data)
                    time.sleep(1)
            except KeyboardInterrupt:
                self._thread.join()


if __name__ == "__main__":
    data = {
        "power": "on",
        "fan_up_and_down": "on",
        "screen": "on",
        "fan_left_and_right": "on",
        "temperature": 20,
        "mode": "cool",
        "fan_speed": "high",
        "key_core": "power"
    }
    refrigeration = Refrigeration(brand="gree")
    while True:
        input("Press Enter to control")
        refrigeration.control(data)