# import cv2
# import numpy as np
# import time
# import threading
# import json
# import copy

# class SmartCam:
#     def __init__(self):
#         self.cap = cv2.VideoCapture(0)
#         self.ret, self.frame = self.cap.read()
#         self.thread = threading.Thread(target=self.__run__)
#         self.thread.start()
#         self.buffer = None

