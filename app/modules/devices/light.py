import os
import copy
import json
import threading
import time

from lightmodule.lightmodule import Light

debug_value = os.environ.get('DEBUG')

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
            self._light = Light(233, 71, 74)
        self._thread = threading.Thread(target=self.__run__, daemon=True)
        self._thread.start()

    def unlock(self):
        self._lock = False

    def __run__(self):
        while self._lock:
            time.sleep(1)
        last_present = copy.deepcopy(self.data["param"]["present"])
        try:
            while True:
                if debug_value == 'True':
                    time.sleep(1)
                    continue
                current_present = self.data["param"]["present"]
                if current_present != last_present:
                    status = current_present.get("status")
                    color = current_present.get("color_rgb", [0, 0, 0])
                    if status == "on":
                        self._light.turn_on(color[0], color[1], color[2])
                    else:
                        self._light.turn_off()
                    last_present = copy.deepcopy(current_present)
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    device = Device()
    device.unlock()
    device.data["param"]["present"]["status"] = "on"
    device.data["param"]["present"]["color_rgb"] = [255, 255, 0]
    time.sleep(5)
    device.data["param"]["present"]["status"] = "off"
    time.sleep(1)
    print("done")

