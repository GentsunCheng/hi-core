import threading
import time
import subprocess


class Notify():
    def __init__(self):
        self._process = None

    def speech(self, message):
        self._process = subprocess.Popen(["espeak-ng", "-v", "zh-cmn", message])

    def stop(self):
        self._process.kill()

class Device():
    def __init__(self):
        self.data = {
            "name": "notify",
            "id": None,
            "type": "virtual_out",
            "readme": "Non-physical device that transmits notifications, warnings, etc",
            "param": {
                "present": {
                    "message": ""
                },
                "selection": {
                    "message": "",
                }
            }
        }
        self.sys_param = {
            "show": False,
            "uuid": "337d0c7d-c5e6-4618-b899-0740a2eb7f37"
        }
        self.trigger = False
        self.init_time = 0
        self._notify = Notify()
        self._thread = threading.Thread(target=self.__run__, daemon=True)
        self._thread.start()

    def __run__(self):
        while True:
            if self.data["param"]["present"]["message"] != "":
                self._notify.stop()
                self._notify.speech(self.data["param"]["present"]["message"])
                self.data["param"]["present"]["message"] = ""
            time.sleep(1)