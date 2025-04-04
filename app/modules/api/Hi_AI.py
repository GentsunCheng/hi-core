import os
import json
import toml
import copy


debug_value = os.environ.get('DEBUG')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

if debug_value == 'False' or debug_value is None:
    from openai import OpenAI


class HIAI_auto:
    def __init__(self, api_key=OPENAI_API_KEY, api_base="https://api.deepseek.com/beta"):
        with open(os.getcwd() + "/source/config.toml", "r", encoding="utf-8") as f:
            config = toml.load(f)
            if config["openai"]["api_key"] != "":
                api_key = config["openai"]["api_key"]
        if debug_value == 'False' or debug_value is None:
            self._client = OpenAI(api_key=api_key, base_url=api_base)
        module_dir = os.path.dirname(__file__)
        tips_path = os.path.join(module_dir, "tips.md")
        with open(tips_path, "r", encoding="utf-8") as f:
            self._tips = f.read()
        self._data = {}
        self._messages = [
            {"role": "system", "content": self._tips},
            {"role": "user", "content": self._data},
            {"role": "assistant", "content": ""},
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "```json\n", "prefix": True}
        ]
        

    def set_data(self, data):
        self._data = data
        self._messages[1]["content"] = data

    def oprate(self, data):
        message = copy.deepcopy(self._messages)
        message[3]["content"] = data
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
            return json.dumps(data)
        else:
            completion  = self._client.chat.completions.create(
                model="deepseek-chat",
                messages=message,
                stream=False,
                stop=["```"],
            )
            return completion.choices[0].message.content


if __name__ == '__main__':
    HIAI = HIAI_auto()
    data = {
    "status": "init",
    "init_param": {
        "designation": "Madis",
        "username": "GentsunCheng",
        "custom": "No need to be energy efficient, but you need to be comfortable, no light when you sleep, and absolute silence."
    },
    "devices":
        [
            {
                "name": "语音通知",
                "id": 0,
                "readme": "Non-physical devices that transmit voice notifications, warnings, and other information. Note that you need to convert the units of measure to text.",
                "type": "virtual_out",
                "param": {
                    "present": {
                        "message": "",
                        "volume": 50
                    },
                    "selection": {
                        "message": "",
                        "volume": ["__RANGE__", 0, 100],
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
                        "skycon": "sunny",
                        "temp": {
                            "outdoor": 33,
                            "apparent":30
                        }
                    },
                    "humidity": 0.83,
                    "wind_speed" : "2km"
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
                        "color_rgb": [64, 127, 255]
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
                "name": "卧室摄像头",
                "id": 8,
                "readme": "The device is a smart camera that detects preset scenarios including, but not limited to, changes in people (e.g., entering and exiting, sleeping, etc.), biological information, and disasters through visual modeling.",
                "type": "smart_sensor",
                "param": {
                    "present": {
                        "message": ""
                    }
                }
            }
        ]
    }
    optdata = [
        {
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
        },
        {
            "status": "trigger",
            "devices":
            [
                {
                    "name": "语音控制",
                    "id": 1,
                    "readme": "Non-physical device through which the user's voice will be entered",
                    "type": "virtual_in",
                    "param": {
                        "present": {
                            "message": "把客厅灯设置成米黄色"
                        }
                    }
                }
            ]
        },
        {
            "status": "trigger",
            "devices":
            [
                {
                    "name": "语音控制",
                    "id": 1,
                    "readme": "Non-physical device through which the user's voice will be entered",
                    "type": "virtual_in",
                    "param": {
                        "present": {
                            "message": "今天天气咋样"
                        }
                    }
                }
            ]
        },
        {
            "status": "trigger",
            "devices":
            [
                {
                    "name": "卧室摄像头",
                    "id": 8,
                    "readme": "The device is a smart camera that detects preset scenarios including, but not limited to, changes in people (e.g., entering and exiting, sleeping, etc.), biological information, and disasters through visual modeling.",
                    "type": "smart_sensor",
                    "param": {
                        "present": {
                            "message": "The user is sleeping."
                        }
                    }
                }
            ]
        }
    ]

    HIAI.set_data(json.dumps(data))
    for opt in optdata:
        content = HIAI.oprate(json.dumps(opt))
        print(content)
