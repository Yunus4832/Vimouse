from queue import Queue
from threading import Thread, Semaphore
from time import sleep
from typing import Tuple
from pynput import keyboard

import pyautogui


class KeyboardInterceptor(Thread):
    """
    全局的键盘按键拦截器
    """

    def __init__(self, actionQueue: Queue[Tuple[int, Tuple[int, int, int]]], pressedKeySet: set[int], stopSet: set[int]):
        super().__init__()
        self.__actionQueue: Queue[Tuple[int, Tuple[int, int, int]]] = actionQueue
        self.__pressedKeys: set[int] = pressedKeySet
        self.__stopSet: set[int] = stopSet
        self.__pauseSemaphore = Semaphore(1)
        self.__listener = None
        self.__isPressShift = False
        self.__isPressMeta = False
        self.__isPressCtrl = False
        self.__isPressAlt = False
        self.__enable = False
        self.name = "KeyboardInterceptor"
        self.daemon = True

    def run(self) -> None:
        with keyboard.Listener(win32_event_filter=self.__filter, suppress=False) as self.__listener:
            self.__listener.join()

    def stop(self) -> None:
        self.__listener.stop()

    def pause(self) -> None:
        """
        暂停监听键盘
        """
        self.__pauseSemaphore.acquire()
        self.__isPressShift = False
        self.__isPressMeta = False
        self.__isPressCtrl = False
        self.__isPressAlt = False
        self.__enable = False
        self.__pressedKeys.clear()
        self.__pauseSemaphore.release()
        # 修复功能键同 CapsLock 一同按下导致的回到 Insert 模式而功能键不释放的问题
        pyautogui.keyUp("ctrl")
        pyautogui.keyUp("alt")
        pyautogui.keyUp("shift")

    def goon(self) -> None:
        """
        继续监听键盘
        """
        self.__pauseSemaphore.acquire()
        self.__stopSet.clear()
        self.__enable = True
        self.__pauseSemaphore.release()

    def isEnable(self) -> bool:
        """
        返回是否开启拦截器
        """
        return self.__enable

    def __filter(self, msg, data) -> None:
        # 如果暂停，停止拦截键盘，并记录下此时按下的按键集合, 释放按键时清除按键
        if not self.__enable:
            if msg == 256 or msg == 260:
                self.__stopSet.add(data.vkCode)
            if msg == 257 or msg == 261:
                if data.vkCode in self.__stopSet:
                    self.__stopSet.discard(data.vkCode)
            if data.vkCode == 20:
                self.__listener.suppress_event()
            return

        # 记录是否按下 Meta
        if data.vkCode == 91:
            if msg == 256:
                self.__isPressMeta = True
            else:
                self.__isPressMeta = False
            return

        # 不拦截包含 Meta 的键
        if self.__isPressMeta:
            return

        # 记录是否按下 Ctrl
        if data.vkCode & 0b11111110 == 162:
            if msg == 256:
                self.__isPressCtrl = True
            else:
                self.__isPressCtrl = False
            self.__listener.suppress_event()

        # 记录是否按下 Shift
        if data.vkCode & 0b11111110 == 160:
            if msg == 256:
                self.__isPressShift = True
            else:
                self.__isPressShift = False
            self.__listener.suppress_event()

        # 记录是否按下了 Alt
        if data.vkCode & 0b11111110 == 164:
            if msg == 260:
                self.__isPressAlt = True
            else:
                self.__isPressAlt = False
            self.__listener.suppress_event()

        # 将按下按键时的状态记录一下
        status = (self.__isPressCtrl,
                  self.__isPressShift,
                  self.__isPressAlt)

        # 不拦截 Fn 功能键和数字小键盘
        if data.vkCode & 0b11100000 == 96:
            return

        # 不拦截除 space 以外的其他一些功能键
        if data.vkCode & 0b11110000 == 32:
            if data.vkCode != 32:
                return

        # 不拦截除 enter、tab、backspace的其他键
        if data.vkCode & 0b11100000 == 0:
            # 拦截器启用时 按下大写锁定键将回到插入模式并且切换大写锁定状态
            if msg == 256 and data.vkCode == 20:
                self.pause()
                self.__actionQueue.put((data.vkCode, status))
            if not (data.vkCode == 8 or data.vkCode == 9 or data.vkCode == 13):
                return

        # 释放按键时从已按下按键列表中移除相应按键
        if msg == 257 or msg == 261:
            self.__pressedKeys.discard(data.vkCode)
            self.__listener.suppress_event()

        # 未按下的按键直接放入到动作队列，并加入已按下按键列表中
        if msg == 260 or msg == 256 and data.vkCode not in self.__pressedKeys:
            self.__pressedKeys.add(data.vkCode)
            # 将其放入命令队列中
            self.__actionQueue.put((data.vkCode, status))
            self.__listener.suppress_event()

        # 拦截不释放按键造成的重复按键, 但是不做处理
        self.__listener.suppress_event()


class HistoryRecord:
    """
    历史命令记录器
    """

    def __init__(self):
        self.__history = []
        self.__last = 0
        self.__cursor = 0

    def record(self, option: str) -> None:
        self.__history.append(option)
        self.__last += 1
        self.__cursor = self.__last + 1

    def clear(self) -> None:
        self.__init__()

    def previous(self) -> str:
        self.__cursor = self.__cursor - 1 if self.__cursor > 0 else self.__cursor
        result = self.__history[self.__cursor]
        return result

    def next(self) -> str:
        self.__cursor = self.__cursor + 1 if self.__cursor < self.__last + 1 else self.__last + 1
        return "" if self.__cursor <= self.__last + 1 else self.__history[self.__cursor]


class KeyTranslator:
    """
    将 virtual key 翻译成 ASCII 码字符
    """

    __vk2charMap = {
        (8, False): 8,
        (8, True): 8,
        (9, False): 9,
        (9, True): 9,
        (13, False): 13,
        (13, True): 13,
        (20, False): 20,
        (20, True): 20,
        (27, False): 27,
        (28, True): 27,
        (32, False): 32,
        (32, True): 32,

        (48, False): 48,
        (48, True): 41,
        (49, False): 49,
        (49, True): 33,
        (50, False): 50,
        (50, True): 64,
        (51, False): 51,
        (51, True): 35,
        (52, False): 52,
        (52, True): 36,
        (53, False): 53,
        (53, True): 37,
        (54, False): 54,
        (54, True): 94,
        (55, False): 55,
        (55, True): 38,
        (56, False): 56,
        (56, True): 42,
        (57, False): 57,
        (57, True): 40,

        (186, False): 59,
        (186, True): 58,
        (187, False): 61,
        (187, True): 43,
        (188, False): 44,
        (188, True): 60,
        (189, False): 95,
        (189, True): 45,
        (190, False): 46,
        (190, True): 62,
        (191, False): 47,
        (191, True): 63,
        (192, False): 96,
        (192, True): 126,
        (219, False): 91,
        (219, True): 123,
        (220, False): 92,
        (220, True): 124,
        (221, False): 93,
        (221, True): 125,
        (222, False): 39,
        (222, True): 22
    }

    @classmethod
    def vk2Ascii(cls, key: Tuple[int, tuple]) -> Tuple[int, tuple]:
        """
        获取虚拟键所代表字符的 ASCII 码, 所有输入的字母都转成小写字母, 方便统一按键和按键序列的表示
        """
        if 65 <= key[0] <= 91:
            asciiCode = key[0] + 32
            return asciiCode, key[1]
        asciiCode = cls.__vk2charMap[(key[0], key[1][1])]
        return asciiCode, key[1]

    @classmethod
    def getKeyValue(cls, key: Tuple[int, tuple]) -> str:
        """
        获得 key 的键值，用于执行操作
        """
        temp = cls.vk2Ascii(key)
        ctrl_key = "_c_" if temp[1][0] else ""
        alt_key = "_a_" if temp[1][2] else ""
        shift_key = ""
        if 97 <= temp[0] <= 123 or temp[0] in [8, 9, 13, 20, 27, 32]:
            shift_key = "_s_" if temp[1][1] else ""
        return ctrl_key + shift_key + alt_key + chr(temp[0])

    @classmethod
    def vk2Char(cls, key: Tuple[int, tuple]) -> str:
        """
        获取虚拟键所代表字符
        """
        if 65 <= key[0] <= 91:
            if not key[1][1]:
                asciiCode = key[0] + 32
                return chr(asciiCode)
            asciiCode = key[0]
            return chr(asciiCode)
        return chr(cls.__vk2charMap[(key[0], key[1][1])])


class SpeedRecord(Thread):
    """
    移动速度控制器
    """

    def __init__(self, timeout: int = 5):
        super().__init__()
        self.__timeout = timeout
        self.__count = 0
        self.__semaphore = Semaphore(1)
        self.__speedMap = {
            "fast": 48,
            "normal": 16,
            "slow": 2
        }
        self.__speedList = [key for key in self.__speedMap]
        self.__position = 0
        self.__isRunning = True
        self.daemon = True
        self.name = "SpeedRecord"
        self.start()

    def run(self):
        while self.__isRunning:
            self.__semaphore.acquire()
            self.__count = (self.__count + 1) % self.__timeout
            self.__semaphore.release()
            if self.__count == self.__timeout - 1:
                self.speedNormal()
            sleep(1)

    def speed(self) -> int:
        """
        返回当前速度
        """
        self.__semaphore.acquire()
        self.__count = 0
        self.__semaphore.release()
        return self.__speedMap[self.__speedList[self.__position]]

    def speedUp(self) -> None:
        """
        加速
        """
        self.__position = (self.__position - 1) % len(self.__speedMap)
        self.__semaphore.acquire()
        self.__count = 0
        self.__semaphore.release()

    def speedDown(self) -> None:
        """
        减速
        """
        self.__position = (self.__position + 1) % len(self.__speedMap)
        self.__semaphore.acquire()
        self.__count = 0
        self.__semaphore.release()

    def speedNormal(self) -> None:
        """
        常规速度
        """
        self.__position = 0

    def max(self) -> None:
        """
        最大速度
        """
        self.__position = 0

    def min(self) -> None:
        """
        最小速度
        """
        self.__position = 2
        self.__semaphore.acquire()
        self.__count = 0
        self.__semaphore.release()

    def stop(self):
        """
        停止线程
        """
        self.__isRunning = False


if __name__ == "__main__":
    print("Component Module")
