import os
import json
debug_value = os.environ.get('DEBUG')
API_KEY = os.environ.get('API_KEY')

if debug_value == 'False' or debug_value is None:
    from openai import OpenAI

class HIAI_auto:
    def __init__(self, api_key=API_KEY, api_base="https://api.deepseek.com"):
        if debug_value == 'False' or debug_value is None:
            self.client = OpenAI(api_key=api_key, base_url=api_base)
        module_dir = os.path.dirname(__file__)
        tips_path = os.path.join(module_dir, "tips.md")
        with open(tips_path, "r", encoding="utf-8") as f:
            self.tips = f.read()
        self.messages = [{"role": "system", "content": self.tips}]
        self.data = {}
        self.messages.append({"role": "user", "content": self.data})

    def set_data(self, data):
        self.data = data
        self.messages[1]["content"] = self.data

    def oprate(self, data):
        messages = self.messages
        messages.append({"role": "user", "content": data})
        if debug_value == 'True':
            data = {
                "actions": [
                    {
                    "id": 0,
                        "param": {
                            "selection": {
                                "notification": "Debug message",
                            }
                        }
                    }
                ]
            }
            content = json.dumps(data)
        else:
            completion  = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=self.messages,
                stream=False,
            )
            content = completion.choices[0].message.content
        return content


if __name__ == '__main__':
    HIAI = HIAI_auto()
    data = {
    "status": "init",
    "init_param": {
        "designation": "Madis",
        "custom": "No need to be energy efficient, but you need to be comfortable, no light when you sleep, and absolute silence."
    },
    "devices":
        [
            {
                "name": "终端通知",
                "id": 0,
                "readme": "Non-physical device that transmits notifications, warnings, etc",
                "type": "virtual_out",
                "param": {
                    "selection": {
                        "notification": ""
                    }
                }
            },
            {
                "name": "语音控制",
                "id": 1,
                "readme": "Non-physical device through which the user's voice will be entered",
                "type": "virtual_in",
                "param": {
                    "present": {
                        "message": ""
                    }
                }
            },
            {
                "name": "天气信息",
                "id": 2,
                "readme": "Non-physical device with internet access to current weather",
                "type": "virtual_in",
                "param": {
                    "present": {
                        "status": "sunny",
                        "temp": {
                        "outdoor": 33,
                        "ambient":30
                        }
                    },
                    "humidity": 0.83,
                    "wind_velocity" : "2km"
                    }
                },
                {
                    "name": "卧室灯",
                    "id": 3,
                    "readme": "This device is illuminated with brightness and color control",
                    "type": "light",
                    "param": {
                    "present": {
                        "status": "on",
                        "lightness": 0,
                        "color": "yellow"
                    },
                    "selection": {
                        "status": ["__SELECT__", "on", "off"],
                        "lightness": ["__SELECT__", 0, 1, 2, 3],
                        "color": ["__SELECT__", "yellow", "white"]
                    }
                }
            },
            {
                "name": "客厅灯",
                "id": 4,
                "readme": "This device is illuminated with brightness and color control",
                "type": "light",
                "param": {
                    "present": {
                        "status": "on",
                        "lightness": 0,
                        "color_rgb": "[64, 127, 255]"
                    },
                    "selection": {
                        "status": ["__SELECT__", "on", "off"],
                        "lightness": ["__RANGE__", 0, 100],
                        "color_rgb": [["__RANGE__", 0, 255], ["__RANGE__", 0, 255], ["__RANGE__", 0, 255]]
                    }
                }
            },
            {
                "name": "客厅空调",
                "id": 5,
                "readme": "This unit is an air conditioner with adjustable modes, temperature and air speed",
                "type": "refrigeration",
                "param": {
                    "present": {
                        "status": "off",
                        "temp": 25,
                        "air_velocity": "1",
                        "mode": "cold"
                    },
                    "selection": {
                        "status": ["__SELECT__", "on", "off"],
                        "temp": ["__RANGE__", 16, 30],
                        "air_velocity": ["__SELECT__", 1, 2, 3],
                        "mode": ["__SELECT__", "cold", "hot", "dry", "air_circulate"]
                    }
                }
            },
            {
                "name": "卧室空调",
                "id": 6,
                "readme": "This unit is an air conditioner with adjustable modes, temperature and air speed",
                "type": "refrigeration",
                "param": {
                    "present": {
                        "status": "off",
                        "temp": 28,
                        "air_velocity": "3",
                        "mode": "cold"
                    },
                    "selection": {
                        "status": ["__SELECT__", "on", "off"],
                        "temp": ["__RANGE__", 16, 30],
                        "air_velocity": ["__SELECT__", 1, 2, 3],
                        "mode": ["__SELECT__", "cold", "hot", "dry", "air_circulate"]
                    }
                }
            },
            {
                "name": "二氧化碳传感器",
                "id": 7,
                "readme": "This device is a carbon dioxide sensor to view carbon dioxide concentration",
                "type": "sensor",
                "param": {
                    "present": {
                        "content": 400,
                        "measure": "ppm"
                    }
                }
            },
            {
                "name": "客厅摄像头",
                "id": 8,
                "readme": "This device is a smart camera that detects changes in people (e.g., entry/exit, sleep, etc.), biological information, and disaster situations",
                "type": "smart_sensor",
                "param": {
                    "present": {
                        "message": ""
                    }
                }
            }
        ]
    }
    optdata = {
    "status": "trigger",
    "devices":
        [
            {
                "name": "二氧化碳传感器",
                "id": 7,
                "readme": "This device is a carbon dioxide sensor to view carbon dioxide concentration",
                "type": "sensor",
                "param": {
                    "present": {
                        "content": 700,
                        "measure": "ppm"
                    }
                }
            }
        ]
    }
    HIAI.set_data(json.dumps(data))
    content = HIAI.oprate(json.dumps(optdata))
    print(content)


