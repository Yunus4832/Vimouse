# -*- coding: UTF-8 -*-
from enum import Enum
from functools import wraps
from queue import Queue
from threading import Thread, Event
from time import sleep
from typing import Tuple
from pynput import keyboard

import pyautogui
import ctypes

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Vimouse")


def execInThread(func):
    """
    让方法在一个新线程中执行的修饰器
    """
    @wraps(func)
    def wrap(*args, **kwargs):
        Thread(target=func, args=args, kwargs=kwargs).start()

    return wrap


class KeyboardInterceptor(Thread):
    """
    全局的键盘按键拦截器
    """
    def __init__(self, actionQueue: Queue, pressedKeySet: set):
        super().__init__()
        self.__actionQueue = actionQueue
        self.__pressedKeys = pressedKeySet
        self.__listener = None
        self.__isPressShift = False
        self.__isPressMeta = False
        self.__isPressCtrl = False
        self.__isPressAlt = False
        self.__enable = True

    def run(self) -> None:
        with keyboard.Listener(win32_event_filter=self.__filter, suppress=False) as self.__listener:
            self.__listener.join()

    def stop(self) -> None:
        self.__listener.stop()

    def pause(self):
        """
        暂停监听键盘
        """
        self.__enable = False

    def goon(self):
        """
        继续监听键盘
        """
        self.__enable = True

    def __filter(self, msg, data) -> None:
        # 该键不可配置，固定为 CAPSLOCK
        if data.vkCode == 20:
            self.__enable = True
            self.__listener.suppress_event()

        # 如果暂停，停止拦截键盘
        if not self.__enable:
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

        # 不拦截 Fn 功能键和数字小键盘
        if data.vkCode & 0b11100000 == 96:
            return

        # 不拦截除 space 以外的其他一些功能键
        if data.vkCode & 0b11110000 == 32:
            if data.vkCode != 32:
                return

        # 不拦截除 enter、tab、backspace 的其他键
        if data.vkCode & 0b11100000 == 0:
            if not (data.vkCode == 8 or data.vkCode == 9 or data.vkCode == 13):
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

        # 释放按键时从已按下按键列表中移除响应按键
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


class Mode(Enum):
    """
    不同的模式
    """
    NORMAL = "normal"
    COMMAND = "command"
    # 实际实现时并未使用如下模式，这里只是记录下 vimouse 可能的模式，
    # 因为可能存在更好的实现方式，只是我暂时没有想到。
    INSERT = "insert"
    VISUAL = "visual"


class Name(Enum):
    """
    给 寄存器 和 标签 使用的名称枚举
    """
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"
    # 最近使用的记录
    RECENT = "'"
    # 剪切板
    CLIP_BOARD = "CLIP_BOARD"


class HistoryRecord:
    """
    历史命令记录器
    """
    def __init__(self):
        self.__history = []
        self.__last = 0
        self.__cursor = 0

    def record(self, option: str):
        self.__history.append(option)
        self.__last += 1
        self.__cursor = self.__last + 1

    def clear(self):
        self.__init__()

    def previous(self):
        self.__cursor = self.__cursor - 1 if self.__cursor > 0 else self.__cursor
        result = self.__history[self.__cursor]
        return result

    def next(self):
        self.__cursor = self.__cursor + 1 if self.__cursor < self.__last + 1 else self.__last + 1
        return "" if self.__cursor <= self.__last + 1 else self.__history[self.__cursor]


class KeyTranslator:
    """
    将 virtual key 翻译成 ASCII 码字符
    """
    def __init__(self):
        self.__vk2charMap = {
            (8, False): 8,
            (8, True): 8,
            (9, False): 9,
            (9, True): 9,
            (13, False): 13,
            (13, True): 13,
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

    def vk2Char(self, key: Tuple[int, tuple]):
        if 65 <= key[0] <= 91:
            if not key[1][1]:
                asciiCode = key[0] + 32
                return asciiCode, key[1]
            asciiCode = key[0]
            return asciiCode, key[1]
        asciiCode = self.__vk2charMap[(key[0], key[1][1])]
        return asciiCode, key[1]


class SystemBase:
    """
    包装系统底层提供的接口
    """
    @classmethod
    def getPosition(cls):
        """
        获取屏幕鼠标位置
        """
        return pyautogui.position()

    @classmethod
    def moveTo(cls, x: int, y: int, during: float = 0.1):
        """
        跳转到屏幕位置
        :param x:  x 轴坐标
        :param y:  y 轴坐标
        :param during:  动作完成时间
        """
        pyautogui.moveTo(x, y, during)

    @classmethod
    def getScreenSize(cls):
        """
        获取屏幕尺寸
        :return: 返回屏幕尺寸的元组 (x, y)
        """
        return pyautogui.size()

    @classmethod
    @execInThread
    def moveUp(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        向上移动
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.move(0, -1 * offset * distance, during)

    @classmethod
    @execInThread
    def moveDown(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        向下移动
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.move(0, offset * distance, during)

    @classmethod
    @execInThread
    def moveLeft(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        向左移动
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.move(-1 * offset * distance, 0, during)

    @classmethod
    @execInThread
    def moveRight(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        向右移动
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.move(offset * distance, 0, during)

    @classmethod
    @execInThread
    def scrollUp(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        滚轮上滚
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.scroll(offset * distance, during)

    @classmethod
    @execInThread
    def scrollDown(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        滚轮下滚
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.scroll(-1 * offset * distance, during)

    @classmethod
    @execInThread
    def clickLeft(cls) -> None:
        """
        点击鼠标左键
        """
        pyautogui.leftClick()

    @classmethod
    @execInThread
    def clickRight(cls) -> None:
        """
        点击鼠标右键
        """
        pyautogui.rightClick()

    @classmethod
    @execInThread
    def clickMiddle(cls) -> None:
        """
        点击鼠标中键
        """
        pyautogui.middleClick()

    @classmethod
    def pressPrimary(cls):
        """
        按住鼠标左键
        """
        pyautogui.mouseDown()

    @classmethod
    def releasePrimary(cls):
        """
        释放鼠标左键
        """
        pyautogui.mouseUp()

    @classmethod
    def yank(cls):
        """
        复制内容
        """
        pyautogui.hotkey("ctrl", "c")

    @classmethod
    def paste(cls):
        """
        黏贴内容
        """
        pyautogui.hotkey("ctrl", "v")

    @classmethod
    def hotkey(cls, *hotkeys: str):
        """
        向系统发送快捷键
        :param hotkeys: 快捷键序列
        """
        pyautogui.hotkey(*hotkeys)

    @classmethod
    def keyDown(cls, key: str):
        """
        按下键盘中的一个按键不释放
        :param key: 需要按下的按键
        """
        pyautogui.keyDown(key)

    @classmethod
    def keyUp(cls, key: str):
        """
        释放键盘中的一个按键不释放
        :param key: 需要释放的按键
        """
        pyautogui.keyUp(key)


class Action(Enum):
    """
    动作枚举
    """
    MOVE_LEFT = ("move_left", SystemBase.moveLeft, (72,))
    MOVE_RIGHT = ("move_right", SystemBase.moveRight, (76,))
    MOVE_UP = ("move_up", SystemBase.moveUp, (75,))
    MOVE_DOWN = ("move_down", SystemBase.moveDown, (74,))
    SCROLL_UP = ("scroll_up", SystemBase.scrollUp, (66, 75))
    SCROLL_DOWN = ("scroll_down", SystemBase.scrollDown, (70, 74))


class SpeedRecord:
    """
    移动速度控制器
    """
    def __init__(self):
        self.__speedMap = {
            "fast": 32,
            "normal": 8,
            "slow": 2
        }
        self.__speedList = [key for key in self.__speedMap]
        self.__position = 0

    def speed(self):
        return self.__speedMap[self.__speedList[self.__position]]

    def speedUp(self):
        self.__position = (self.__position - 1) % len(self.__speedMap)

    def speedDown(self):
        self.__position = (self.__position + 1) % len(self.__speedMap)

    def speedNormal(self):
        self.__position = 0

    def max(self):
        self.__position = 0

    def min(self):
        self.__position = 2


class Mover(Thread):
    """
    移动控制器
    """
    def __init__(self, event: Event, moveSet: set, pressedKeySet: set, speedRecord: SpeedRecord):
        super().__init__()
        self.__moveSignal = event
        self.__moveSet = moveSet
        self.__pressedKeySet = pressedKeySet
        self.__roundTable = set()
        self.__speedRecord = speedRecord

    def run(self):
        while True:
            if len(self.__moveSet) == 0:
                self.__moveSignal.clear()
                self.__moveSignal.wait()
            self.__roundTable.clear()
            self.__move()
            self.__moveSignal.clear()
            self.__moveSignal.wait(0.01)

    def __move(self):
        # copy 防止 set 遍历时修改 set 导致的异常
        for action in self.__moveSet.copy():
            flag = True
            for keyCode in action.value[2]:
                if keyCode in self.__pressedKeySet:
                    flag = False
                    break
            if flag:
                self.__moveSet.discard(action)
                return
            if action in self.__moveSet and action not in self.__roundTable:
                self.__roundTable.add(action)
                action.value[1](1, self.__speedRecord.speed())


class VimController(Thread):
    """
    vim 控制器
    """
    def __init__(self):
        super().__init__()
        # 默认所在的模式
        self.__mode = Mode.NORMAL
        # 所有的寄存器
        self.__register = {key: "" for key in Name}
        # 所有的标记
        self.__mark = {key: (0, 0) for key in Name}
        # 反查 Name 字典
        self.__name = {chr(key): value for key, value in zip(range(65, 92), Name)}
        # 记录最近跳转位置
        self.__name["'"] = Name.RECENT
        self.__name["`"] = Name.RECENT
        # 默认按键映射
        self.__keyMap = {
            "m": self.doMark,
            "'": self.goMark,
            "`": self.goMark,
            "c_b": self.scrollUp,
            "c_f": self.scrollDown,
            "\r": self.clickLeft,
            "c_\r": self.clickMiddle,
            "a_\r": self.clickRight,
            "j": self.moveDown,
            "k": self.moveUP,
            "h": self.moveLeft,
            "l": self.moveRight,
            "a_j": self.scrollDown,
            "a_k": self.scrollUp,
            "c_a": self.speedMin,
            "a_a": self.speedMax,
            "a": self.speedDown,
            "i": self.insert,
            "v": self.visual
        }
        # 自定义按键映射
        self.__customKeyMap = {}
        # 用于接收键盘拦截器传过来的按键
        self.__actionQueue = Queue()
        # 用于记录即将要触发的鼠标动作集合
        self.__moveKeySet = set()
        # 用于存储键盘上持续按下的按键集合
        self.__pressedKeySet = set()

        # 键盘拦截器
        self.__keyboardInterceptor = KeyboardInterceptor(self.__actionQueue, self.__pressedKeySet)

        # 键翻译器
        self.__keyTranslator = KeyTranslator()

        # 控制移动的事件, 用于同步移动线程
        self.__moveSignal = Event()
        # 速度控制器
        self.__speedRecord = SpeedRecord()
        # 鼠标移动模拟器
        self.__mover = Mover(self.__moveSignal, self.__moveKeySet, self.__pressedKeySet, self.__speedRecord)

    def run(self):
        self.__keyboardInterceptor.start()
        self.__mover.start()
        while True:
            key = self.__keyTranslator.vk2Char(self.__actionQueue.get())
            if self.__mode == Mode.NORMAL or self.__mode == Mode.VISUAL:
                keyValue = self.getKeyValue(key)
                if keyValue not in self.__keyMap or self.__keyMap[keyValue] is None:
                    continue
                self.__keyMap[keyValue]()
                continue

    def doMark(self):
        key = self.__actionQueue.get()
        keyChar = chr(self.__keyTranslator.vk2Char(key)[0]).upper()
        markName = self.__name[keyChar]
        pos = SystemBase.getPosition()
        self.__mark[markName] = pos

    def goMark(self):
        key = self.__actionQueue.get()
        keyChar = chr(self.__keyTranslator.vk2Char(key)[0]).upper()
        markName = self.__name[keyChar] if keyChar in self.__name else None
        if markName is None:
            return
        pos = SystemBase.getPosition()
        if markName is Name.RECENT:
            SystemBase.moveTo(*self.__mark[markName])
            self.__mark[Name.RECENT] = pos
            return
        self.__mark[Name.RECENT] = pos
        SystemBase.moveTo(*self.__mark[markName])

    def scrollUp(self):
        self.__moveKeySet.add(Action.SCROLL_UP)
        self.__moveSignal.set()

    def scrollDown(self):
        self.__moveKeySet.add(Action.SCROLL_DOWN)
        self.__moveSignal.set()

    def moveDown(self):
        self.__moveKeySet.add(Action.MOVE_DOWN)
        self.__moveSignal.set()

    def moveUP(self):
        self.__moveKeySet.add(Action.MOVE_UP)
        self.__moveSignal.set()

    def moveLeft(self):
        self.__moveKeySet.add(Action.MOVE_LEFT)
        self.__moveSignal.set()

    def moveRight(self):
        self.__moveKeySet.add(Action.MOVE_RIGHT)
        self.__moveSignal.set()

    def speedMax(self):
        self.__speedRecord.max()

    def speedMin(self):
        self.__speedRecord.min()

    def speedDown(self):
        self.__speedRecord.speedDown()

    def stop(self):
        pass

    def visual(self):
        if self.__mode != Mode.VISUAL:
            self.__mode = Mode.VISUAL
            SystemBase.pressPrimary()
            return
        SystemBase.releasePrimary()
        self.__mode = Mode.NORMAL

    def insert(self):
        sleep(0.2)
        self.__keyboardInterceptor.pause()
        self.__pressedKeySet.clear()

    @classmethod
    def clickLeft(cls):
        SystemBase.clickLeft()

    @classmethod
    def clickRight(cls):
        SystemBase.clickRight()

    @classmethod
    def clickMiddle(cls):
        SystemBase.clickMiddle()

    @classmethod
    def getKeyValue(cls, key: Tuple[int, tuple]):
        ctrl_key = "c_" if key[1][0] else ""
        shift_key = "s_" if key[1][1] else ""
        alt_key = "a_" if key[1][2] else ""
        return ctrl_key + shift_key + alt_key + chr(key[0])


# 测试代码
if __name__ == "__main__":
    controller = VimController()
    controller.start()
