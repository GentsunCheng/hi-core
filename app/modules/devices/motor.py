import time
import json
import copy
import threading
from periphery import GPIO

class StepperMotorHalfStep:
    def __init__(self, pins, gpiochip="/dev/gpiochip0", steps_per_revolution=4096):
        """
        初始化步进电机控制类（半步模式）
        :param pins: 四个引脚编号的列表，例如 [70, 69, 72, 231]
        :param gpiochip: GPIO 芯片路径，例如 "/dev/gpiochip0"
        :param steps_per_revolution: 每转一圈所需的步数，默认 4096（适用于 28BYJ-48）
        """
        self.gpiochip = gpiochip
        self.pins = pins
        self.steps_per_revolution = steps_per_revolution
        # 初始化 GPIO 引脚
        self.gpios = [GPIO(gpiochip, pin, "out") for pin in pins]
        # ULN2003 半步序列（8步）
        self.step_sequence = [
            [1, 0, 0, 0],
            [1, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 1],
            [1, 0, 0, 1]
        ]
        # 定义转速挡位对应的延时（秒）
        self.speed_levels = {0: 0.002, 1: 0.001, 2: 0.0008}
        self.running = False
        self.thread = None

    def rotate(self, rotations=0, speed_level=0, direction="cw"):
        """
        开始旋转步进电机（半步模式）
        :param rotations: 旋转圈数，传 0 表示无限旋转（直到调用 stop()）
        :param speed_level: 转速挡位，0: 最慢 (0.002s延时), 1: 中速 (0.001s延时), 2: 快速 (0.0008s延时)
        :param direction: 旋转方向，"cw" 为顺时针，"ccw" 为逆时针
        """
        delay = self.speed_levels.get(speed_level, 0.002)
        # 根据方向选择步进序列（逆时针时反转序列）
        step_seq = self.step_sequence if direction == "cw" else self.step_sequence[::-1]

        self.running = True

        def run():
            steps_moved = 0
            # 计算目标步数（如果 rotations 大于0）
            target_steps = int(rotations * self.steps_per_revolution) if rotations > 0 else None
            try:
                while self.running:
                    for step in step_seq:
                        if not self.running:
                            break
                        # 写入每个 GPIO 引脚状态（确保传入 bool 类型）
                        for gpio, state in zip(self.gpios, step):
                            gpio.write(state == 1)
                        time.sleep(delay)
                        steps_moved += 1
                        if target_steps is not None and steps_moved >= target_steps:
                            self.running = False
                            break
            finally:
                # 旋转结束后关闭所有 GPIO
                self.cleanup_gpio()

        # 使用线程执行旋转，避免阻塞主程序
        self.thread = threading.Thread(target=run)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()
        self.cleanup_gpio()

    def cleanup_gpio(self):
        """关闭所有 GPIO 并释放资源"""
        for gpio in self.gpios:
            gpio.write(False)

class StepperMotorFullStep:
    def __init__(self, pins, gpiochip="/dev/gpiochip0", steps_per_revolution=2048):
        self.gpiochip = gpiochip
        self.pins = pins
        self.steps_per_revolution = steps_per_revolution
        self.gpios = [GPIO(gpiochip, pin, "out") for pin in pins]
        self.step_sequence = [
            [1, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 1],
            [1, 0, 0, 1]
        ]
        self.speed_levels = {0: 0.0025, 1: 0.002, 2: 0.0015}
        self.running = False
        self.thread = None

    def rotate(self, rotations=0, speed_level=0, direction="cw"):
        delay = self.speed_levels.get(speed_level, 0.0025)
        step_seq = self.step_sequence if direction == "cw" else self.step_sequence[::-1]
        self.running = True

        def run():
            steps_moved = 0
            target_steps = int(rotations * self.steps_per_revolution) if rotations > 0 else None
            try:
                while self.running:
                    for step in step_seq:
                        if not self.running:
                            break
                        for gpio, state in zip(self.gpios, step):
                            gpio.write(state == 1)
                        time.sleep(delay)
                        steps_moved += 1
                        if target_steps is not None and steps_moved >= target_steps:
                            self.running = False
                            break
            finally:
                # 旋转结束后关闭所有 GPIO
                self.cleanup_gpio()

        self.thread = threading.Thread(target=run)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()
        self.cleanup_gpio()

    def cleanup_gpio(self):
        """关闭所有 GPIO 并释放资源"""
        for gpio in self.gpios:
            gpio.write(False)

    def __del__(self):
        for gpio in self.gpios:
            gpio.close()

class Device:
    def __init__(self):
        self.data = {
            "name": "draperies",
            "id": None,
            "type": "draperies",
            "readme": "This unit is an actuator that controls the draperies. It can be used to open or close the draperies.",
            "param": {
                "present": {
                    "status": "open"
                },
                "selection": {
                    "status": ["__SELECT__", "open", "closed"],
                }
            }
        }
        self.uuid = "c3cdd2f0-e9e2-4853-8baf-a99a5fefaabc"
        self.trigger = False
        self.init_time = 0
        self.motor = StepperMotorFullStep([70, 69, 72, 79])
        self._thread = threading.Thread(target=self.__run__)
        self._thread.start()

    def __run__(self):
        data = copy.deepcopy(self.data)
        try:
            while True:
                if json.dumps(self.data["param"]["present"], sort_keys=True) != json.dumps(data["param"]["present"], sort_keys=True):
                    if self.data["param"]["present"]["status"] == "open":
                        self.motor.stop()
                        self.motor.rotate(rotations=5, speed_level=2, direction="cw")
                    elif self.data["param"]["present"]["status"] == "closed":
                        self.motor.stop()
                        self.motor.rotate(rotations=5, speed_level=2, direction="ccw")
                    data = copy.deepcopy(self.data)
                time.sleep(1)
        except KeyboardInterrupt:
            self._thread.join()



# 使用示例
if __name__ == "__main__":
    # 请根据你的电机实际步数设置 steps_per_revolution，
    # 全步模式下28BYJ-48大约为2048步/圈
    motor = StepperMotorFullStep([70, 69, 72, 231])
    try:
        # 示例：旋转 2 圈，中速，顺时针方向
        motor.rotate()
        # 如果设置 rotations=0，则电机会无限旋转，直到调用 stop()
        if motor.thread is not None:
            motor.thread.join()
    except KeyboardInterrupt:
        print("检测到中断信号，停止电机。")
    finally:
        motor.stop()
