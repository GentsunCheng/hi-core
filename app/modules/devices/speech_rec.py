import time
import threading


class SpeechRec():
    def __init__(self):
        self.speeched = False
        pass
    
    def get_text(self):
        pass

    def __fill_text_buf__(self):
        pass

class Device():
    def __init__(self):
        self.data = {
            "name": "speech_recognation",
            "id": None,
            "type": "virtual_in",
            "readme": "Non-physical device through which the user's voice will be entered",
            "param": {
                "present": {
                    "message": ""
                }
            }
        }
        self.sys_param = {
            "show": False,
            "uuid": "a3eca894-18a2-49d6-b22d-5fd36feac911"
        }
        self.trigger = False
        self.init_time = 0
        self.speechrec = SpeechRec()
        self._thread = threading.Thread(target=self.__run__)
        self._thread.start()

    def __run__(self):
        while True:
            if self.speechrec.speeched:
                self.data["param"]["present"]["message"] = self.speechrec.get_text()
                self.trigger = True
                while self.trigger:
                    time.sleep(0.5)
                self.data["param"]["present"]["message"] = ""
            if self.data["param"]["present"]["message"] != "":
                self.trigger = True
                while self.trigger:
                    time.sleep(0.5)
                self.data["param"]["present"]["message"] = ""
            time.sleep(1)