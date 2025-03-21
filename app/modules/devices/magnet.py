import time
import threading
from periphery import GPIO

class Electromagnet:
    def __init__(self, pin, gpiochip="/dev/gpiochip0"):
        """
        初始化电磁铁控制器.
        :param pin: GPIO引脚号
        :param gpiochip: GPIO芯片路径，例如 "/dev/gpiochip0"
        """
        self._gpio = GPIO(gpiochip, pin, "out")
        self._thread = None
        self._stop_event = threading.Event()

    def start(self, duration=0):
        """
        启动电磁铁.
        :param duration: 启动时间，单位秒。为0时表示持续启动直到手动停止。
        """
        if self._thread is not None and self._thread.is_alive():
            print("电磁铁已在运行中。")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_magnet, args=(duration,), daemon=True)
        self._thread.start()

    def _run_magnet(self, duration):
        try:
            # 激活电磁铁
            self._gpio.write(True)
            if duration > 0:
                # 等待指定时间或直到收到停止信号
                finished = self._stop_event.wait(timeout=duration)
                # 如果超时（即在 duration 内未收到停止信号），自动关闭电磁铁
                if not finished:
                    self._gpio.write(False)
            else:
                # duration 为0时，持续等待直到收到停止信号
                self._stop_event.wait()
                self._gpio.write(False)
        except Exception as e:
            print(f"运行电磁铁时发生错误: {e}")
        finally:
            # 确保电磁铁关闭
            self._gpio.write(False)

    def stop(self):
        """
        停止电磁铁.
        """
        if self._thread is not None and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join()
            self._thread = None
        # 确保电磁铁关闭
        self._gpio.write(False)

    def __del__(self):
        self._gpio.close()

class Device():
    def __init__(self):
        self.data = {
            "name": "door",
            "id": None,
            "type": "door",
            "readme": "This is a door. It can be used to open and close the door.",
            "param": {
                "present": {
                    "status": "closed"
                },
                "selection": {
                    "status": ["__SELECT__", "open"],
                }
            }
        }
        self.sys_param = {
            "show": True,
            "uuid": "4f836a1a-eedd-4d93-8258-63b1fb74e610"
        }
        self.trigger = False
        self.init_time = 0
        self._magnet = Electromagnet(231)
        self._thread = threading.Thread(target=self.__run__, daemon=True)
        self._thread.start()

    def __run__(self):
        run_time = 0
        try:
            while True:
                if self.data["param"]["present"]["status"] == "opened":
                    run_time += 1
                if run_time > 15:
                    self.data["param"]["present"]["status"] = "closed"
                    run_time = 0
                if self.data["param"]["present"]["status"] == "open" and run_time <= 15:
                    self.data["param"]["present"]["status"] = "opened"
                    print("open door")
                    self._magnet.start(duration=15)
                    run_time = 0
                time.sleep(1)
        except KeyboardInterrupt:
            self._thread.join()
        finally:
            self._magnet.stop()


if __name__ == "__main__":
    # 假设 GPIO 芯片为 "/dev/gpiochip0"，引脚号为 226
    magnet = Electromagnet(226)

    try:
        magnet.start()
        # 模拟主程序运行
        time.sleep(10)
    except KeyboardInterrupt:
        print("程序被中断。")
    finally:
        magnet.stop()
