import threading
import time
import sounddevice as sd
import soundfile as sf
from gtts import gTTS
from io import BytesIO

class Notify:
    def __init__(self):
        # 播放控制
        self._playing = False
        self._thread = None

    def speech(self, message):
        """ 使用 gTTS 生成音频并播放 """
        # 生成语音
        tts = gTTS(text=message, lang='zh')
        
        # 将音频保存到内存中（无需保存为文件）
        audio_stream = BytesIO()
        tts.write_to_fp(audio_stream)
        audio_stream.seek(0)  # 返回到文件开头

        # 读取音频数据
        data, samplerate = sf.read(audio_stream)

        # 启动音频播放线程
        self._playing = True
        self._thread = threading.Thread(target=self._play_audio, args=(data, samplerate))
        self._thread.start()

    def _play_audio(self, data, samplerate):
        """ 播放音频（可打断） """
        sd.play(data, samplerate)
        while self._playing and sd.get_stream().active:
            pass  # 保持线程运行，等待播放完成
        sd.stop()  # 确保音频停止
        self._playing = False

    def stop(self):
        """ 停止当前播放的音频 """
        if self._playing:
            self._playing = False
            sd.stop()
            if self._thread and self._thread.is_alive():
                self._thread.join()
        

class Device():
    def __init__(self):
        self.data = {
            "name": "notify",
            "id": None,
            "type": "virtual_out",
            "readme": "Non-physical device that transmits notifications, warnings, etc",
            "param": {
                "present": {
                    "message": ""
                },
                "selection": {
                    "message": "",
                }
            }
        }
        self.sys_param = {
            "show": False,
            "uuid": "337d0c7d-c5e6-4618-b899-0740a2eb7f37"
        }
        self.trigger = False
        self.init_time = 0
        self._notify = Notify()
        self._thread = threading.Thread(target=self.__run__, daemon=True)
        self._thread.start()

    def __run__(self):
        while True:
            if self.data["param"]["present"]["message"] != "":
                self._notify.stop()
                self._notify.speech(self.data["param"]["present"]["message"])
                self.data["param"]["present"]["message"] = ""
            time.sleep(1)

if __name__ == "__main__":
    notify = Notify()
    text = "你好，你好啊"
    notify.speech(text)
    