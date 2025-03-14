import threading
import time


class Notify():
    def __init__(self):
        pass

    def speech(self, message):
        pass

    def stop(self):
        pass

    def __tts__(self):
        pass

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
        self.uuid = "3c51ef5f-b525-4413-ac35-02d1152f7e1a"
        self.action = False
        self.init_time = 0
        self.notify = Notify()
        self._thread = threading.Thread(target=self.__run__)
        self._thread.start()

    def __run__(self):
        while True:
            if self.data["param"]["present"]["message"] != "":
                self.notify.stop()
                self.notify.speech(self.data["param"]["present"]["message"])
                self.data["param"]["present"]["message"] = ""
            time.sleep(1)