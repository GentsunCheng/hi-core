import os
import cv2
import time
import requests
import shutil
import threading
from ultralytics import YOLO

class SmartCam:
    def __init__(self):
        self._cap = cv2.VideoCapture("/dev/video1", cv2.CAP_V4L2)
        self._frame = None
        model_path = os.getcwd() + "/source/yolo11n.pt"
        if not os.path.exists(model_path):
            print("Model not found, start Download...")
            url = "https://static.orii.top/yolo11n.pt"
            with requests.get(url, stream=True) as response:
                with open(model_path, "wb") as file:
                    shutil.copyfileobj(response.raw, file)
            print("Download finished")
        self._complete = False
        self._inited = False
        self._detect_old = {
            "person": 0,
            "fire": 0
        }
        self._detect_last = {
            "person": 0,
            "fire": 0
        }
        self._detect_time_old = {
            "person": time.time(),
            "fire": time.time()
        }
        self._model = YOLO(model=str(model_path))
        self._thread = threading.Thread(target=self._get_image, daemon=True)
        self._thread.start()


    def _get_image(self, fps=0.2):
        width, height = 640, 480
        device = "/dev/video1"
        while True:
            try:
                _, self._frame = self._cap.read()
                time.sleep(1 / fps)
                if self._frame is None:
                    continue
                self._complete = True
                results = self._model(self._frame)
                person_count = 0
                fire_count = 0
                for result in results:
                    if hasattr(result, "boxes") and result.boxes is not None:
                        for cls in result.boxes.cls.cpu().numpy():
                            label = self._model.names[int(cls)]                       
                            if label.lower() == "person":
                                person_count += 1
                            elif label.lower() == "fire":
                                fire_count += 1
                self._detect_last["person"] = person_count
                self._detect_last["fire"] = fire_count

            except Exception as e:
                print(e)
                time.sleep(1)

    def _init_data(self):
        while not self._complete:
            time.sleep(1)
        self._detect_old["person"] = self._detect_last["person"]
        self._detect_old["fire"] = self._detect_last["fire"]
        self._inited = True

    def check_person(self, waittime=60):
        while not self._inited:
            time.sleep(1)
        current_time = time.time()
        if self._detect_old["person"] > 0 and self._detect_last["person"] == 0:
            if current_time - self._detect_time_old["person"] > waittime:
                self._detect_time_old["person"] = current_time
                self._detect_old["person"] = 0
                return 'left'
        elif self._detect_old["person"] == 0 and self._detect_last["person"] > 0:
            self._detect_time_old["person"] = current_time
            self._detect_old["person"] = self._detect_last["person"]
            return 'enter'
        elif self._detect_old["person"] > 0 and self._detect_last["person"] > 0:
            self._detect_time_old["person"] = current_time
            self._detect_old["person"] = self._detect_last["person"]
            return 'stay'
        elif self._detect_old["person"] == 0 and self._detect_last["person"] == 0:
            self._detect_time_old["person"] = current_time
            self._detect_old["person"] = 0
            return 'none'
        else:
            return None


    def check_fire(self, waittime=60):
        while not self._inited:
            time.sleep(1)
        current_time = time.time()
        if self._detect_old["fire"] == 0 and self._detect_last["fire"] > 0:
            if current_time - self._detect_time_old["fire"] > waittime:
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
            "uuid": "012f3cda-9fa3-4d8b-8194-081e2671491f"
        }
        self.trigger = False
        self.init_time = 0
        self._smartcam = SmartCam()
        self._thread = threading.Thread(target=self.__run__, daemon=True)
        self._thread.start()

    def __run__(self):
        while True:
            person_status = self._smartcam.check_person()
            fire_status = self._smartcam.check_fire()
            if person_status == "left":
                self.data["param"]["present"]["message"] = "Person left"
                self.trigger = True
            if person_status == "enter":
                self.data["param"]["present"]["message"] = "Person enter"
                self.trigger = True
            if person_status == "stay":
                self.data["param"]["present"]["message"] = "Person inside"
            if person_status == "none":
                self.data["param"]["present"]["message"] = "No person"
            if fire_status == True:
                self.data["param"]["present"]["message"] = "Burning fire"
                self.trigger = True
            time.sleep(1)


