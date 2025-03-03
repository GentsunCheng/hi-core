import sys
import json
import time
import threading
from openai import OpenAI

class HI_api:
    def __init__(self, data, api_key="sk-a906b49c4fae4c5d8cf21f391bfc7153", api_base="https://api.deepseek.com"):
        self.client = OpenAI(api_key=api_key, base_url=api_base)
        with open("tips.md", "r", encoding="utf-8") as f:
            self.tips = f.read()
        self.messages = [{"role": "system", "content": self.tips}]
        self.messages.append({"role": "user", "content": data})
        self.data = data
        self.need_change = False
        self.running = True
        self.th1 = threading.Thread(target=self.__change__)
        self.th1.start()
    
    def __change__(self):
        while self.running:
            if self.need_change:
                self.messages[1]["content"] = self.data
                self.need_change = False
            time.sleep(0.5)

    def oprate(self, data):
        self.messages.append({"role": "user", "content": data})
        completion  = self.client.chat.completions.create(
            model="deepseek-reasoner",
            messages=self.messages,
            stream=False,
        )
        content = completion.choices[0].message.content
        return content

