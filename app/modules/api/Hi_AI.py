import os
import json
debug_value = os.environ.get('DEBUG')

if debug_value == 'False' or debug_value is None:
    from openai import OpenAI

class HIAI_auto:
    def __init__(self, api_key="sk-a906b49c4fae4c5d8cf21f391bfc7153", api_base="https://api.deepseek.com"):
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

