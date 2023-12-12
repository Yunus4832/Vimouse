# -*- coding: UTF-8 -*-
from enum import Enum
from queue import Queue
from threading import Thread, Event
from time import sleep
from typing import Tuple, Callable
from component import KeyboardInterceptor, SpeedRecord, KeyTranslator
from utils.commonUtils import execInThread, Timer, FileLock

import re
import sys
import pyautogui
import ctypes

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Vimouse")


# todo
# - [x] 选择模式
#   - [x] ~~右键菜单连续移动~~
#   - [x] 选择模式 esc || q 退出后回到普通模式
# - [ ] 鼠标分区块移动功能
# - [ ] 实现命令模式
# - [ ] 状态栏显示状态
# - [ ] 历史命令记录
# - [ ] 寄存器实现
# - [x] 计时器实现
# - [ ] 水平滚轮实现 (pyautogui 只支持 Linux 水平滚动)
# - [ ] 四叉树定位：H 左上，K 右上，J 左下，L 右下, Q 回到上一级
# - [x] go 命令实现：gg 回到原点、gc 回到中心、ge 回到最大点、zt|z<enter>回到顶部、zz 回到中间、zb 回到底部


class Mode(Enum):
    """
    不同的模式枚举, 不同的模式具有不同的按键映射
    """

    # 普通模式
    NORMAL = "normal"
    # 命令模式
    COMMAND = "command"
    # 选择模式
    SELECT = "select"
    # 输入模式
    INSERT = "insert"
    # 框选模式
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


class SystemBase:
    """
    包装系统底层提供的接口
    """

    @classmethod
    def getPosition(cls) -> tuple:
        """
        获取屏幕鼠标位置
        """
        return pyautogui.position()

    @classmethod
    def moveTo(cls, x, y, during: float = 0.1) -> None:
        """
        跳转到屏幕位置
        :param x:  x 轴坐标
        :param y:  y 轴坐标
        :param during:  动作完成时间
        """
        pyautogui.moveTo(int(x), int(y), during)

    @classmethod
    def getScreenSize(cls) -> Tuple[int, int]:
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
    def scrollLeft(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        滚轮左移
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.hscroll(offset * distance, during)

    @classmethod
    @execInThread
    def scrollRight(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        滚轮右移
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.hscroll(-1 * offset * distance, during)

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
    def pressPrimary(cls) -> None:
        """
        按住鼠标左键
        """
        pyautogui.mouseDown()

    @classmethod
    def releasePrimary(cls) -> None:
        """
        释放鼠标左键
        """
        pyautogui.mouseUp()

    @classmethod
    def yank(cls) -> None:
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
    def hotkey(cls, *hotkeys: str, times: int = 1) -> None:
        """
        向系统发送快捷键
        :param times: 按键次数
        :param hotkeys: 快捷键序列
        """
        for i in range(0, times):
            pyautogui.hotkey(*hotkeys)

    @classmethod
    def keyDown(cls, key: str) -> None:
        """
        按下键盘中的一个按键不释放
        :param key: 需要按下的按键
        """
        pyautogui.keyDown(key)

    @classmethod
    def keyUp(cls, key: str) -> None:
        """
        释放键盘中的一个按键不释放
        :param key: 需要释放的按键
        """
        pyautogui.keyUp(key)


class Action(Enum):
    """
    动作枚举
    """
    # 移动 action
    MOVE_LEFT = ("move_left", SystemBase.moveLeft, (72,), 1, (1,))
    MOVE_RIGHT = ("move_right", SystemBase.moveRight, (76,), 1, (1,))
    MOVE_UP = ("move_up", SystemBase.moveUp, (75,), 1, (1,))
    MOVE_DOWN = ("move_down", SystemBase.moveDown, (74,), 1, (1,))
    SCROLL_UP = ("scroll_up", SystemBase.scrollUp, (66, 75), 1, (1,))
    SCROLL_DOWN = ("scroll_down", SystemBase.scrollDown, (70, 74), 1, (1,))
    SCROLL_LEFT = ("scroll_left", SystemBase.scrollLeft, (76,), 1, (1,))
    SCROLL_RIGHT = ("scroll_right", SystemBase.scrollRight, (72,), 1, (1,))

    # 按键映射 action
    NEXT = ("next", SystemBase.hotkey, (74,), 2, ("down",))
    PREVIOUS = ("previous", SystemBase.hotkey, (75,), 2, ("up",))
    FORWARD = ("forward", SystemBase.hotkey, (76,), 2, ("right",))
    BACKWARD = ("backward", SystemBase.hotkey, (72,), 2, ("left",))

    def __init__(self, name: str, action: Callable, relatedKey: tuple, actionType: int, param: tuple):
        self._name = name
        self._action = action
        self._relatedKey = relatedKey
        self._actionType = actionType
        self._param = param

    @property
    def name(self) -> str:
        """
        名称
        """
        return self._name

    @property
    def exec(self) -> Callable:
        """
        触发动作
        """
        return self._action

    @property
    def relatedKey(self) -> tuple:
        """
        相关的 vk-code
        """
        return self._relatedKey

    @property
    def actionType(self) -> int:
        """
        动作类型, 1 -> 移动, 2 -> 按键映射
        """
        return self._actionType

    @property
    def param(self) -> tuple:
        """
        参数
        """
        return self._param


class ActionHandler(Thread):
    """
    Action 处理器
    """

    def __init__(self, event: Event, moveSet: set, pressedKeySet: set, speedRecord: SpeedRecord):
        super().__init__()
        self.__moveSignal = event
        self.__moveSet = moveSet
        self.__pressedKeySet = pressedKeySet
        self.__speedRecord = speedRecord

    def run(self):
        while True:
            if len(self.__moveSet) == 0:
                self.__moveSignal.clear()
                self.__moveSignal.wait()
            self.__move()
            self.__moveSignal.clear()
            self.__moveSignal.wait(0.01)

    def __move(self):
        # copy 防止 set 遍历时修改 set 导致的异常
        for action in self.__moveSet.copy():
            flag = True
            for keyCode in action.relatedKey:
                if keyCode in self.__pressedKeySet:
                    flag = False
                    break
            if flag:
                self.__moveSet.discard(action)
                return

            # 如果类型是 1, 代表移动, 调用时需要附加速度
            if action.actionType == 1:
                action.exec(action.param[0], self.__speedRecord.speed())

            # 如果类型是 2, 代表按键映射
            if action.actionType == 2:
                action.exec(action.param[0])
                sleep(0.1)


class Controller(Thread):
    """
    vim 控制器
    """

    def __init__(self):
        super().__init__()
        # 屏幕宽高
        self.__screenWidth, self.__screenHeight = SystemBase.getScreenSize()
        # 默认所在的模式
        self.__mode = Mode.NORMAL
        # 进入普通模式的过期时间
        self.__normalTimeout = 60
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
        self.__keyMaps = {
            Mode.NORMAL: {
                "m": self.doMark,
                "'": self.goMark,
                "`": self.goMark,
                "_c_b": self.scrollUp,
                "_c_f": self.scrollDown,
                "\r": self.clickLeft,
                "_c_\r": self.clickMiddle,
                "_a_\r": self.clickRight,
                "_a_\t": self.taskToggle,
                "j": self.moveDown,
                "k": self.moveUP,
                "h": self.moveLeft,
                "l": self.moveRight,
                "_a_j": self.scrollDown,
                "_a_k": self.scrollUp,
                "_a_h": self.scrollLeft,
                "_a_l": self.scrollRight,
                "_c_a": self.speedMin,
                "_a_a": self.speedMax,
                "a": self.speedDown,
                "i": self.insert,
                "_s_i": self.insertWithClick,
                "v": self.visual,
                "s": self.selectItem,
                "_a_ ": self.windowMenu,
                "gg": self.goZero,
                "gc": self.goCenter,
                "ge": self.goEnd,
                "zt": self.goTop,
                "z\r": self.goTop,
                "zz": self.goMiddle,
                "zb": self.goBottom
            },
            Mode.SELECT: {
                "j": self.next,
                "k": self.previous,
                "h": self.backward,
                "l": self.forward,
                "\r": self.confirmSelect,
                "q": self.quitSelect,
                "_s_q": self.quitSelectWithESC
            },
            Mode.VISUAL: {
                "'": self.goMark,
                "`": self.goMark,
                "_c_b": self.scrollUp,
                "_c_f": self.scrollDown,
                "j": self.moveDown,
                "k": self.moveUP,
                "h": self.moveLeft,
                "l": self.moveRight,
                "_a_j": self.scrollDown,
                "_a_k": self.scrollUp,
                "_a_h": self.scrollLeft,
                "_a_l": self.scrollRight,
                "_c_a": self.speedMin,
                "_a_a": self.speedMax,
                "a": self.speedDown,
                "v": self.visual,
                "gg": self.goZero,
                "gc": self.goCenter,
                "ge": self.goEnd,
                "zt": self.goTop,
                "z\r": self.goTop,
                "zz": self.goMiddle,
                "zb": self.goBottom
            },
            Mode.INSERT: {},
            Mode.COMMAND: {}
        }
        # 自定义按键映射
        self.__customKeyMap = {}
        # 用于接收键盘拦截器传过来的按键
        self.__actionQueue = Queue()
        # 用于记录即将要触发的鼠标动作集合
        self.__moveKeySet = set()
        # 用于存储键盘上持续按下的按键集合
        self.__pressedKeySet = set()
        # 用于存放停止监听键盘时的按键集合
        self.__stopSet = set()
        # 定时器，用于超时后自动退出到插入模式
        self.__timer = Timer()
        # 命令重复次数
        self.__commandTimes = 1

        # 键盘拦截器
        self.__keyboardInterceptor = KeyboardInterceptor(self.__actionQueue, self.__pressedKeySet, self.__stopSet)

        # 控制移动的事件, 用于同步移动线程
        self.__moveSignal = Event()
        # 速度控制器
        self.__speedRecord = SpeedRecord()
        # Action 处理器
        self.__actionHandler = ActionHandler(
            self.__moveSignal,
            self.__moveKeySet,
            self.__pressedKeySet,
            self.__speedRecord
        )

    def run(self):
        self.__keyboardInterceptor.start()
        self.__actionHandler.start()
        while True:
            if self.__keyboardInterceptor.isEnable():
                if self.__timer.isRun():
                    key = KeyTranslator.getKeyValue(self.__actionQueue.get())
                    cmd = self.__matchCommand("", key)
                    if cmd not in self.__keyMaps[self.__mode] or self.__keyMaps[self.__mode][cmd] is None:
                        continue
                    self.__keyMaps[self.__mode][cmd]()
                    self.__timer.reset()
                    continue
                else:
                    self.__mode = Mode.INSERT
                    self.__keyboardInterceptor.pause()
                    self.__pressedKeySet.clear()
                continue
            if 20 in self.__stopSet:
                self.__mode = Mode.NORMAL
                self.__timer = Timer(self.__normalTimeout)
                self.__timer.start()
                self.__stopSet.clear()
                self.__keyboardInterceptor.goon()
                continue
            sleep(0.05)

    def doMark(self):
        """
        在鼠标当前位置做标记
        """
        key = self.__actionQueue.get()
        keyChar = chr(KeyTranslator.vk2Char(key)[0]).upper()
        markName = self.__name[keyChar]
        pos = SystemBase.getPosition()
        self.__mark[markName] = pos

    def goMark(self):
        """
        将鼠标移动到指定标记
        """
        key = self.__actionQueue.get()
        keyChar = chr(KeyTranslator.vk2Char(key)[0]).upper()
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
        """
        滚轮向上滚动
        """
        self.__moveKeySet.add(Action.SCROLL_UP)
        self.__moveSignal.set()

    def scrollDown(self):
        """
        滚轮向下滚动
        """
        self.__moveKeySet.add(Action.SCROLL_DOWN)
        self.__moveSignal.set()

    def scrollLeft(self):
        """
        滚轮向上滚动
        """
        self.__moveKeySet.add(Action.SCROLL_LEFT)
        self.__moveSignal.set()

    def scrollRight(self):
        """
        滚轮向下滚动
        """
        self.__moveKeySet.add(Action.SCROLL_RIGHT)
        self.__moveSignal.set()

    def moveDown(self):
        """
        鼠标下移
        """
        self.__moveKeySet.add(Action.MOVE_DOWN)
        self.__moveSignal.set()

    def moveUP(self):
        """
        鼠标上移
        """
        self.__moveKeySet.add(Action.MOVE_UP)
        self.__moveSignal.set()

    def moveLeft(self):
        """
        鼠标左移
        """
        self.__moveKeySet.add(Action.MOVE_LEFT)
        self.__moveSignal.set()

    def moveRight(self):
        """
        鼠标右移
        """
        self.__moveKeySet.add(Action.MOVE_RIGHT)
        self.__moveSignal.set()

    def speedMax(self):
        """
        将移动速度调整到最大
        """
        self.__speedRecord.max()

    def speedMin(self):
        """
        将移动速度调整到最小
        """
        self.__speedRecord.min()

    def speedDown(self):
        """
        减小移动速度

        """
        self.__speedRecord.speedDown()

    def stop(self):
        pass

    def visual(self):
        """
        进入可视模式
        """
        if self.__mode != Mode.VISUAL:
            self.__mode = Mode.VISUAL
            SystemBase.pressPrimary()
            return
        SystemBase.releasePrimary()
        self.__mode = Mode.NORMAL

    def insert(self):
        """
        进入插入模式
        """
        self.__mode = Mode.INSERT
        self.__keyboardInterceptor.pause()
        self.__pressedKeySet.clear()
        self.__timer.stop()

    def insertWithClick(self):
        """
        点击左键并进入插入模式
        """
        self.__mode = Mode.INSERT
        self.clickLeft()
        self.__keyboardInterceptor.pause()
        self.__pressedKeySet.clear()
        self.__timer.stop()

    @classmethod
    def clickLeft(cls):
        """
        鼠标左键
        """
        SystemBase.clickLeft()

    def clickRight(self):
        """
        鼠标右键
        """
        SystemBase.clickRight()
        self.selectItem()

    def taskToggle(self):
        self.__keyboardInterceptor.pause()
        SystemBase.keyDown("alt")
        SystemBase.hotkey("tab")
        self.__stopSet.add(164)
        while 164 in self.__stopSet or 165 in self.__stopSet:
            sleep(0.1)
            continue
        SystemBase.keyUp("alt")
        self.__timer = Timer(self.__normalTimeout)
        self.__timer.start()
        self.__stopSet.clear()
        self.__keyboardInterceptor.goon()

    def windowMenu(self):
        """
        打开窗口菜单
        """
        self.__pressKey("alt", "space")
        self.selectItem()

    def goZero(self):
        """
        光标回到原点
        """
        SystemBase.moveTo(0, 0)

    def goCenter(self):
        """
        光标回到中心
        """
        width, height = SystemBase.getScreenSize()
        SystemBase.moveTo(width / 2, height / 2)

    def goEnd(self):
        """
        回到最大点
        """
        screenWidth, screenHeight = SystemBase.getScreenSize()
        SystemBase.moveTo(screenWidth, screenHeight)

    def goTop(self):
        """
        回到顶部
        """
        width, height = SystemBase.getPosition()
        SystemBase.moveTo(x=width, y=self.__screenHeight * 0.01)

    def goMiddle(self):
        """
        回到中间
        """
        width, height = SystemBase.getPosition()
        SystemBase.moveTo(x=width, y=self.__screenHeight / 2)

    def goBottom(self):
        """
        回到底部
        """
        width, height = SystemBase.getPosition()
        SystemBase.moveTo(x=width, y=self.__screenHeight * 0.99)

    def selectItem(self):
        """
        用于在菜单中选择的模式
        """
        self.__mode = Mode.SELECT
        return

    def next(self):
        """
        下一个
        """
        self.__moveKeySet.add(Action.NEXT)
        self.__moveSignal.set()

    def previous(self):
        """
        上一个
        """
        self.__moveKeySet.add(Action.PREVIOUS)
        self.__moveSignal.set()

    def forward(self):
        """
        向前
        """
        self.__moveKeySet.add(Action.FORWARD)
        self.__moveSignal.set()

    def backward(self):
        """
        后退
        """
        self.__moveKeySet.add(Action.BACKWARD)
        self.__moveSignal.set()

    def confirmSelect(self):
        """
        确认选项
        """
        self.__pressKey("enter")

    def quitSelect(self):
        """
        退出选择模式
        """
        self.__mode = Mode.NORMAL

    def quitSelectWithESC(self):
        """
        退出选择模式, 并按下 ESC 键
        """
        self.__pressKey("esc")
        self.__mode = Mode.NORMAL

    @classmethod
    def clickMiddle(cls):
        """
        鼠标中键
        """
        SystemBase.clickMiddle()

    def __getKeyAction(self) -> list:
        key = self.__actionQueue.get()
        result = []
        if key[1][0]:
            result.append("ctrl")
        if key[1][1]:
            result.append("shift")
        if key[1][2]:
            result.append("alt")
        result.append(chr(KeyTranslator.vk2Char(key)[0]))
        return result

    def __pressKey(self, *key: str, times: int = 1):
        self.__keyboardInterceptor.pause()
        SystemBase.hotkey(*key, times=times)
        self.__keyboardInterceptor.goon()

    def __matchCommand(self, first: str, second: str) -> str:
        """
        通过递归的方式匹配命令
        """
        temp = first + second
        pattern = re.compile('^"|\'' + temp)
        cmdList = [cmd for cmd in self.__keyMaps[self.__mode].keys()]
        result = pattern.findall(str(cmdList))
        if len(result) > 1:
            key = KeyTranslator.getKeyValue(self.__actionQueue.get())
            return self.__matchCommand(temp, key)
        return temp


# 启动代码
if __name__ == "__main__":
    # 通过文件锁保证系统中只存在一个 Vimouse 进程，文件锁默认保存在系统临时目录中（C:/Temp/Vimouse.lock)
    try:
        lock = FileLock("C:/Temp/Vimouse.lock")
        lock.acquire()
    except RuntimeError:
        sys.exit()
    controller = Controller()
    controller.start()
