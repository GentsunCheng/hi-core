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
            "custom": "No need to be energy efficient, but you need to be comfortable, no light when you sleep, and absolute silence.",
            "designation": "Madis",
            "username": "GentsunCheng"
        },
        "devices": [
            {
                "name": "draperies",
                "id": 0,
                "type": "draperies",
                "readme": "This unit is an actuator that controls the draperies. It can be used to open or close the draperies.",
                "param": {
                    "present": {
                    "status": "closed"
                    },
                    "selection": {
                    "status": [
                        "__SELECT__",
                        "open",
                        "closed"
                    ]
                    }
                }
            },
            {
                "name": "speech_recognation",
                "id": 1,
                "type": "virtual_in",
                "readme": "Non-physical device through which the user's voice will be entered",
                "param": {
                    "present": {
                    "message": ""
                    }
                }
            },
            {
                "name": "refrigeration",
                "id": 2,
                "type": "refrigeration",
                "readme": "This unit is an air conditioner with adjustable modes, temperature and air speed",
                "param": {
                    "present": {
                    "power": "on",
                    "fan_up_and_down": "on",
                    "screen": "off",
                    "fan_left_and_right": "on",
                    "temperature": 23,
                    "mode": "cool",
                    "fan_speed": "auto"
                    },
                    "selection": {
                    "power": [
                        "__SELECT__",
                        "off",
                        "on"
                    ],
                    "fan_up_and_down": [
                        "__SELECT__",
                        "off",
                        "on"
                    ],
                    "screen": [
                        "__SELECT__",
                        "off",
                        "on"
                    ],
                    "fan_left_and_right": [
                        "__SELECT__",
                        "off",
                        "on"
                    ],
                    "temperature": [
                        "__RANGE__",
                        16,
                        30
                    ],
                    "mode": [
                        "__SELECT__",
                        "auto",
                        "cool",
                        "dry",
                        "wind",
                        "heat"
                    ],
                    "fan_speed": [
                        "__SELECT__",
                        "auto",
                        "low",
                        "medium",
                        "high"
                    ]
                    }
                }
            },
            {
                "name": "notify",
                "id": 3,
                "type": "virtual_out",
                "readme": "Non-physical device that transmits notifications, warnings, etc",
                "param": {
                    "present": {
                    "message": ""
                    },
                    "selection": {
                    "message": ""
                    }
                }
            },
            {
                "name": "door",
                "id": 4,
                "type": "door",
                "readme": "This is a door. It can be used to open and close the door.",
                "param": {
                    "present": {
                    "status": "closed"
                    },
                    "selection": {
                    "status": [
                        "__SELECT__",
                        "open"
                    ]
                    }
                }
            },
            {
                "name": "rgb_light",
                "id": 5,
                "type": "light",
                "readme": "This unit is an actuator that controls the rgb light. It can be used to change the color of the light.",
                "param": {
                    "present": {
                    "status": "off",
                    "color_rgb": [
                        255,
                        8,
                        255
                    ]
                    },
                    "selection": {
                    "status": [
                        "__SELECT__",
                        "on",
                        "off"
                    ],
                    "color_rgb": [
                        [
                            "__RANGE__",
                            0,
                            255
                        ],
                        [
                            "__RANGE__",
                            0,
                            255
                        ],
                        [
                            "__RANGE__",
                            0,
                            255
                        ]
                    ]
                    }
                }
            },
            {
                "name": "smartcam",
                "id": 6,
                "type": "virtual_in",
                "readme": "Non-physical device through which the user's voice will be entered",
                "param": {
                    "present": {
                    "message": ""
                    }
                }
            },
            {
                "name": "multi_sensor",
                "id": 7,
                "type": "sensor",
                "readme": "Its a multi sensor to measure CO2, TVOC, Light, Temperature and Humidity",
                "param": {
                    "present": {
                    "co2": {
                        "content": 400,
                        "measure": "ppm"
                    },
                    "tvoc": {
                        "content": 0,
                        "measure": "ppb"
                    },
                    "light": {
                        "content": 0,
                        "measure": "lx"
                    },
                    "temperature": {
                        "content": 25,
                        "measure": "°C"
                    },
                    "humidity": {
                        "content": 70,
                        "measure": "%"
                    }
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
                    "name": "multi_sensor",
                    "id": 7,
                    "readme": "Its a multi sensor to measure CO2, TVOC, Light, Temperature and Humidity",
                    "type": "sensor",
                    "param": {
                        "present": {
                            "co2": {
                                "content": 1129,
                                "measure": "ppm"
                            },
                            "tvoc": {
                                "content": 3,
                                "measure": "ppb"
                            },
                            "light": {
                                "content": 221.3,
                                "measure": "lx"
                            },
                            "temperature": {
                                "content": 26.3,
                                "measure": "°C"
                            },
                            "humidity": {
                                "content": 82.5,
                                "measure": "%"
                            }
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
                    "name": "speech_recognation",
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
                    "name": "speech_recognation",
                    "id": 1,
                    "readme": "Non-physical device through which the user's voice will be entered",
                    "type": "virtual_in",
                    "param": {
                        "present": {
                            "message": "打开窗帘"
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
    # for opt in optdata:
    #     content = HIAI.oprate(json.dumps(opt))
    #     print("Tigger data: ", opt)
    #     print("Response command: ", content)
    i = int(input("测试项目:")) + 1
    content = HIAI.oprate(json.dumps(optdata[i]))
    print("触发数据: ", optdata[i])
    print("响应指令: ", content)
