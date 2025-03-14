import os
import time
import requests
import threading
import shutil
import geoip2.database
import toml


class Weather():
    def __init__(self, api_key=None, api_base="https://api.caiyunapp.com"):
        self.api_key = api_key
        with open(os.getcwd() + "/source/config.toml", "r", encoding="utf-8") as f:
            config = toml.load(f)
            if config["weather"]["api_key"] != "":
                self.api_key = config["weather"]["api_key"]
        self.api_base = api_base
        self.version = "v2.6"
        self.location = self.__get_location__()
        

    def __get_location__(self):
        filename = os.getcwd() + '/source/GeoLite2-City.mmdb'
        if not os.path.exists(filename):
            print("GeoLite2-City.mmdb not found, start Download...")
            url = "https://static.orii.top/GeoLite2-City.mmdb"
            with requests.get(url, stream=True) as response:
                with open(filename, "wb") as file:
                    shutil.copyfileobj(response.raw, file)
            print("Download finished")

        ip = requests.get('http://4.ipw.cn').text
        reader = geoip2.database.Reader(filename)
        response = reader.city(ip)
        reader.close()
        return str(response.location.longitude) + "," + str(response.location.latitude)

    def get_weather_info(self):
        response = requests.get(f"{self.api_base}/{self.version}/{self.api_key}/{self.location}/realtime")
        if response.status_code == 200:
            data = response.json()["result"]["realtime"]
            skycon = data["skycon"]
            temp = str(data["temperature"]) + "°C"
            apparent_temp = str(data["apparent_temperature"]) + "°C"
            humidity = str(data["humidity"]) + "%"
            wind_speed = str(data["wind"]["speed"]) + "km/h"
            return skycon, temp, apparent_temp, humidity, wind_speed
        else:
            return None


class Device():
    def __init__(self):
        self.data = {
            "name": "weather_info",
            "id": None,
            "type": "virtual_in",
            "readme": "Non-physical device with internet access to current weather",
            "param": {
                "present": {
                    "skycon": "UNKNOWN",
                    "temp": {
                        "outdoor": "27°C",
                        "apparent":"27°C"
                    },
                    "humidity": "0.75%",
                    "wind_speed" : "0km/h"
                }
            }
        }
        self.uuid = "2c03700e-4765-4173-ba91-014baa55013e"
        self.action = False
        self.init_time = 0
        self.weather = Weather()
        self.__get_weather__()
        self.duration = 1.5
        self._thread = threading.Thread(target=self.__run__)
        self._stop_event = threading.Event()
        self._thread.start()

    def __get_weather__(self):
        data = self.weather.get_weather_info()
        if data is None:
            return
        self.data["param"]["present"]["skycon"] = data[0]
        self.data["param"]["present"]["temp"]["outdoor"] = data[1]
        self.data["param"]["present"]["temp"]["apparent"] = data[2]
        self.data["param"]["present"]["humidity"] = data[3]
        self.data["param"]["present"]["wind_speed"] = data[4]

    def __run__(self):
        while True:
            for _ in range(int(self.duration * 3600)):
                self._stop_event.wait(1)
                if self._stop_event.is_set():
                    return
                time.sleep(1)
            self.__get_weather__()
            self.action = True
            


if __name__ == "__main__":
    device = Device()
    print(device.data)