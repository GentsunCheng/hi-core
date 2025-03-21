import os
import cv2
import time
import requests
import shutil
import threading
from ultralytics import YOLO

class SmartCam:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.ret, self.frame = self.cap.read()
        self.thread = threading.Thread(target=self.__run__)
        self.thread.start()
        self.frame = None
        model_path = os.getcwd() + "/source/yolo8n.pt"
        if not os.path.exists(model_path):
            print("Model not found, start Download...")
            url = "https://static.orii.top/yolo8n.pt"
            with requests.get(url, stream=True) as response:
                with open(model_path, "wb") as file:
                    shutil.copyfileobj(response.raw, file)
            print("Download finished")
        self.detect_old = {
            "person": 0,
            "fire": 0
        }
        self.detect_last = {
            "person": 0,
            "fire": 0
        }
        self.detect_time_old = {
            "person": time.time(),
            "fire": time.time()
        }
        self.model = YOLO(model_path)
        self._thread = threading.Thread(target=self._get_image, daemon=True)
        self._thread.start()


    def _get_image(self, fps=0.2):
        while True:
            try:
                self.ret, self.frame = self.cap.read()
                time.sleep(1 / fps)
                if self.frame is None:
                    continue
                results = self.model(self.frame)
                person_count = 0
                fire_count = 0
                for result in results:
                    if hasattr(result, "boxes") and result.boxes is not None:
                        for cls in result.boxes.cls.cpu().numpy():
                            label = self.model.names[int(cls)]
                            if label.lower() == "person":
                                person_count += 1
                            elif label.lower() == "fire":
                                fire_count += 1
                self.detect_last["person"] = person_count
                self.detect_last["fire"] = fire_count

            except Exception as e:
                print(e)
                time.sleep(1)

    def check_person(self, waittime=60):
        current_time = time.time()
        if self.detect_old["person"] > 0 and self.detect_last["person"] == 0:
            if current_time - self.detect_time_old["person"] > waittime:
                self.detect_time_old["person"] = current_time
                self.detect_old["person"] = 0
                return 'left'
        elif self.detect_old["person"] == 0 and self.detect_last["person"] > 0:
            self.detect_time_old["person"] = current_time
            self.detect_old["person"] = self.detect_last["person"]
            return 'enter'
        else:
            return None


    def check_fire(self, waittime=60):
        current_time = time.time()
        if self.detect_old["fire"] == 0 and self.detect_last["fire"] > 0:
            if current_time - self.detect_time_old["fire"] > waittime:
                return True
        else:
            return False

class Device:
    def __init__(self):
        self.data = {
            "name": "smartcam",
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
        self._smartcam = SmartCam()
        self._thread = threading.Thread(target=self.__run__, daemon=True)
        self._thread.start()

    def __run__(self):
        while True:
            if self._smartcam.check_person() == "left":
                self.data["param"]["present"]["message"] = "Person left"
                self.trigger = True
            if self._smartcam.check_person() == "enter":
                self.data["param"]["present"]["message"] = "Person enter"
                self.trigger = True
            if self._smartcam.check_fire() == True:
                self.data["param"]["present"]["message"] = "Burning fire"
                self.trigger = True
            time.sleep(1)


