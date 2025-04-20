import os
import copy
import json
import threading
import time

debug_value = os.environ.get('DEBUG')
if debug_value == 'False' or debug_value is None:
    from periphery import GPIO
    class Light:
        def __init__(self, pins, gpiochip="/dev/gpiochip0"):
            self._rgb = {
                "red": 0,
                "green": 0,
                "blue": 0
            }
            self._sorted_rgb = copy.deepcopy(self._rgb)
            self._gpios = {
                "red": GPIO(gpiochip, pins[0], "out"),
                "green": GPIO(gpiochip, pins[1], "out"),
                "blue": GPIO(gpiochip, pins[2], "out")
            }
            self._lock = False
            self._running = False
            self._thread = threading.Thread(target=self._run_, daemon=True)
            self._thread.start()

        def turn_on(self, rgb=[255, 255, 255]):
            while self._lock:
                time.sleep(0.1)
            self._lock = True
            self._rgb["red"] = rgb[0]
            self._rgb["green"] = rgb[1]
            self._rgb["blue"] = rgb[2]
            self._sorted_rgb = dict(sorted(self._rgb.items(), key=lambda item: item[1]))
            self._running = True
            self._lock = False

        def turn_off(self):
            while self._lock:
                time.sleep(0.1)
            self._lock = True
            if self._running:
                self._running = False
                for value in self._gpios.values():
                    value.write(False)
            self._lock = False

        def _run_(self):
            while True:
                if not self._running:
                    time.sleep(0.3)
                    continue
                time_run = 0
                for color, value in self._gpios.items():
                    if self._sorted_rgb[color]:
                        value.write(True)
                for color, value in self._sorted_rgb.items():
                    time.sleep((value - time_run) / 255)
                    self._gpios[color].write(False)
                    time_run = value
                time.sleep((255 - time_run) / 255)

class Device:
    def __init__(self):
        self.data = {
            "name": "rgb_light",
            "id": None,
            "type": "light",
            "readme": "This unit is an actuator that controls the rgb light. It can be used to change the color of the light.",
            "param": {
                "present": {
                    "status": "off",
                    "color_rgb": [255, 255, 255]
                },
                "selection": {
                    "status": ["__SELECT__", "on", "off"],
                    "color_rgb": [["__RANGE__", 0, 255], ["__RANGE__", 0, 255], ["__RANGE__", 0, 255]]
                }
            }
        }
        self.sys_param = {
            "show": True,
            "uuid": "5090e2fe-56df-452f-9b40-7a9c871257c9"
        }
        self.trigger = False
        self.init_time = 0
        self.seed = "x38hdaxggaalglakgzqia69pijeg6p8s"
        self._lock = True
        if debug_value == 'False' or debug_value is None:
            self._light = Light(pins=[233, 71, 74])
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
                if debug_value == 'True':
                    time.sleep(1)
                    continue
                if json.dumps(self.data["param"]["present"], sort_keys=True) != json.dumps(data["param"]["present"], sort_keys=True):
                    if self.data["param"]["present"]["status"] == "on":
                        self._light.turn_on(self.data["param"]["present"]["color_rgb"])
                    elif self.data["param"]["present"]["status"] == "off":
                        self._light.turn_off()
                    data = copy.deepcopy(self.data)
                time.sleep(1)
        except KeyboardInterrupt:
            self._thread.join()


if __name__ == "__main__":
    light = Light(pins=[233, 71, 74])
    light.turn_on([255, 255, 255])
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("done")
