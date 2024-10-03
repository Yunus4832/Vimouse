# -*- coding: UTF-8 -*-
from enum import Enum
from queue import Queue
from threading import Thread, Event
from time import sleep
from typing import Tuple, Callable
from component import KeyboardInterceptor, SpeedRecord, KeyTranslator
from utils.common_utils import exec_in_thread, Timer, FileLock
from utils.gui_utils import Toast

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
# - [x] 实现命令模式
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
    def get_position(cls) -> tuple:
        """
        获取屏幕鼠标位置
        """
        return pyautogui.position()

    @classmethod
    def move_to(cls, x, y, during: float = 0.1) -> None:
        """
        跳转到屏幕位置
        :param x:  x 轴坐标
        :param y:  y 轴坐标
        :param during:  动作完成时间
        """
        pyautogui.moveTo(int(x), int(y), during)

    @classmethod
    def get_screen_size(cls) -> Tuple[int, int]:
        """
        获取屏幕尺寸
        :return: 返回屏幕尺寸的元组 (x, y)
        """
        return pyautogui.size()

    @classmethod
    @exec_in_thread
    def move_up(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        向上移动
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.move(0, -1 * offset * distance, during)

    @classmethod
    @exec_in_thread
    def move_down(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        向下移动
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.move(0, offset * distance, during)

    @classmethod
    @exec_in_thread
    def move_left(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        向左移动
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.move(-1 * offset * distance, 0, during)

    @classmethod
    @exec_in_thread
    def move_right(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        向右移动
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.move(offset * distance, 0, during)

    @classmethod
    @exec_in_thread
    def scroll_up(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        滚轮上滚
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.scroll(offset * distance, during)

    @classmethod
    @exec_in_thread
    def scroll_down(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        滚轮下滚
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.scroll(-1 * offset * distance, during)

    @classmethod
    @exec_in_thread
    def scroll_left(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        滚轮左移
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.hscroll(offset * distance, during)

    @classmethod
    @exec_in_thread
    def scroll_right(cls, distance: int = 1, offset: int = 10, during: float = 0.1) -> None:
        """
        滚轮右移
        :param distance: 移动次数，默认为 1 个单位
        :param offset: 移动偏移量，默认为 10，移动总距离为 distance * offset
        :param during: 移动完成的时间, 默认为 0.1 秒
        """
        pyautogui.hscroll(-1 * offset * distance, during)

    @classmethod
    @exec_in_thread
    def click_left(cls) -> None:
        """
        点击鼠标左键
        """
        pyautogui.leftClick()

    @classmethod
    @exec_in_thread
    def click_right(cls) -> None:
        """
        点击鼠标右键
        """
        pyautogui.rightClick()

    @classmethod
    @exec_in_thread
    def click_middle(cls) -> None:
        """
        点击鼠标中键
        """
        pyautogui.middleClick()

    @classmethod
    def mouse_down(cls, btn: str = "left") -> None:
        """
        按住鼠标左键
        """
        pyautogui.mouseDown(button=btn)

    @classmethod
    def mouse_up(cls, btn: str = "left") -> None:
        """
        释放鼠标左键
        """
        pyautogui.mouseUp(button=btn)

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
    def key_down(cls, key: str) -> None:
        """
        按下键盘中的一个按键不释放
        :param key: 需要按下的按键
        """
        pyautogui.keyDown(key)

    @classmethod
    def key_up(cls, key: str) -> None:
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
    MOVE_LEFT = ("move_left", SystemBase.move_left, (72,), 1, (1,))
    MOVE_RIGHT = ("move_right", SystemBase.move_right, (76,), 1, (1,))
    MOVE_UP = ("move_up", SystemBase.move_up, (75,), 1, (1,))
    MOVE_DOWN = ("move_down", SystemBase.move_down, (74,), 1, (1,))
    SCROLL_UP = ("scroll_up", SystemBase.scroll_up, (66, 75), 1, (1,))
    SCROLL_DOWN = ("scroll_down", SystemBase.scroll_down, (70, 74), 1, (1,))
    SCROLL_LEFT = ("scroll_left", SystemBase.scroll_left, (76,), 1, (1,))
    SCROLL_RIGHT = ("scroll_right", SystemBase.scroll_right, (72,), 1, (1,))

    # 按键映射 action
    NEXT = ("next", SystemBase.hotkey, (74,), 2, ("down",))
    PREVIOUS = ("previous", SystemBase.hotkey, (75,), 2, ("up",))
    FORWARD = ("forward", SystemBase.hotkey, (76,), 2, ("right",))
    BACKWARD = ("backward", SystemBase.hotkey, (72,), 2, ("left",))

    def __init__(self, name: str, action: Callable, related_key: tuple, action_type: int, param: tuple):
        self._name = name
        self._action = action
        self._related_key = related_key
        self._action_type = action_type
        self._param = param

    @property
    def action_name(self) -> str:
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
    def related_key(self) -> tuple:
        """
        相关的 vk-code
        """
        return self._related_key

    @property
    def action_type(self) -> int:
        """
        动作类型, 1 -> 移动, 2 -> 按键映射
        """
        return self._action_type

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

    def __init__(self, event: Event, move_set: set, pressed_key_set: set, speed_record: SpeedRecord):
        super().__init__()
        self.__move_signal = event
        self.__move_set = move_set
        self.__pressed_key_set = pressed_key_set
        self.__speed_record = speed_record
        self.daemon = True
        self.name = "ActionHandler"
        self.__is_running = True

    def run(self):
        while self.__is_running:
            if len(self.__move_set) == 0:
                self.__move_signal.clear()
                self.__move_signal.wait()
            self.__move()
            self.__move_signal.clear()
            self.__move_signal.wait(0.01)

    def __move(self):
        # copy 防止 set 遍历时修改 set 导致的异常
        for action in self.__move_set.copy():
            flag = True
            for key_code in action.related_key:
                if key_code in self.__pressed_key_set:
                    flag = False
                    break
            if flag:
                self.__move_set.discard(action)
                return

            # 如果类型是 1, 代表移动, 调用时需要附加速度
            if action.action_type == 1:
                action.exec(action.param[0], self.__speed_record.speed())

            # 如果类型是 2, 代表按键映射
            if action.action_type == 2:
                action.exec(action.param[0])
                sleep(0.1)

    def stop(self):
        self.__is_running = False


class Controller(Thread):
    """
    vim 控制器
    """

    def __init__(self):
        super().__init__()
        # 屏幕宽高
        self.__screen_width, self.__screen_height = SystemBase.get_screen_size()
        # 默认所在的模式
        self.__mode = Mode.NORMAL
        # 进入普通模式的过期时间
        self.__normal_timeout = 60
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
        self.__key_maps = {
            Mode.NORMAL: {
                "m": self.do_mark,
                "'": self.go_mark,
                "`": self.go_mark,
                "_c_b": self.scroll_up,
                "_c_f": self.scroll_down,
                "\r": self.click_left,
                "_c_\r": self.click_middle,
                "_a_\r": self.click_right,
                "_a_\t": self.task_toggle,
                "_c_\t": self.tab_toggle,
                "j": self.move_down,
                "k": self.move_up,
                "h": self.move_left,
                "l": self.move_right,
                "_a_j": self.scroll_down,
                "_a_k": self.scroll_up,
                "_a_h": self.scroll_left,
                "_c_a": self.speed_min,
                "_a_a": self.speed_max,
                "a": self.speed_down,
                ":": self.command,
                "i": self.insert,
                "_s_i": self.insert_with_click,
                "v": self.visual,
                "_c_v": self.drag,
                "s": self.select_item,
                "_a_ ": self.window_menu,
                "gg": self.go_zero,
                "gc": self.go_center,
                "ge": self.go_end,
                "zt": self.go_top,
                "z\r": self.go_top,
                "zz": self.go_middle,
                "zb": self.go_bottom
            },
            Mode.SELECT: {
                "j": self.next,
                "k": self.previous,
                "h": self.backward,
                "l": self.forward,
                "\r": self.confirm_select,
                "q": self.quit_select_with_esc,
                "_s_q": self.quit_select
            },
            Mode.VISUAL: {
                "'": self.go_mark,
                "`": self.go_mark,
                "_c_b": self.scroll_up,
                "_c_f": self.scroll_down,
                "j": self.move_down,
                "k": self.move_up,
                "h": self.move_left,
                "l": self.move_right,
                "_a_j": self.scroll_down,
                "_a_k": self.scroll_up,
                "_a_h": self.scroll_left,
                "_a_l": self.scroll_right,
                "_c_a": self.speed_min,
                "_a_a": self.speed_max,
                "a": self.speed_down,
                "v": self.visual,
                "_c_v": self.drag,
                "gg": self.go_zero,
                "gc": self.go_center,
                "ge": self.go_end,
                "zt": self.go_top,
                "z\r": self.go_top,
                "zz": self.go_middle,
                "zb": self.go_bottom
            },
            Mode.INSERT: {},
            Mode.COMMAND: {
                "q": self.stop
            }
        }
        # 自定义按键映射
        self.__custom_key_map = {}
        # 用于接收键盘拦截器传过来的按键
        self.__action_queue: Queue[Tuple[int, Tuple[int, int, int]]] = Queue()
        # 用于记录即将要触发的鼠标动作集合
        self.__move_key_set: set[Action] = set()
        # 用于存储键盘上持续按下的按键集合
        self.__pressed_key_set: set[int] = set()
        # 用于存放停止监听键盘时的按键集合
        self.__stop_set: set[int] = set()
        # 定时器，用于超时后自动退出到插入模式
        self.__timer = Timer()
        # 命令重复次数
        self.__command_times = 1
        # 消息显示 Toast
        screen_size = SystemBase.get_screen_size()
        self.__toast = Toast(position_x=0, position_y=int(screen_size[1] * 0.9), width=screen_size[0], height=30)

        # 键盘拦截器
        self.__keyboard_interceptor = KeyboardInterceptor(self.__action_queue, self.__pressed_key_set, self.__stop_set)

        # 控制移动的事件, 用于同步移动线程
        self.__move_signal = Event()
        # 速度控制器
        self.__speed_record = SpeedRecord()
        # Action 处理器
        self.__action_handler = ActionHandler(
            self.__move_signal,
            self.__move_key_set,
            self.__pressed_key_set,
            self.__speed_record
        )
        # 是否退出标志
        self.__is_running = True
        self.name = "Controller"

    def run(self):
        self.__keyboard_interceptor.start()
        self.__action_handler.start()
        self.__toast.start()
        while self.__is_running:
            if self.__keyboard_interceptor.is_enable():
                if self.__timer.isRun():
                    if self.__mode == Mode.NORMAL or self.__mode == Mode.VISUAL:
                        key = KeyTranslator.get_key_value(self.__action_queue.get())
                        cmd = self.__match_command("", key)
                        if cmd not in self.__key_maps[self.__mode] or self.__key_maps[self.__mode][cmd] is None:
                            continue
                        self.__key_maps[self.__mode][cmd]()
                        self.__timer.reset()
                        continue
                    if self.__mode == Mode.SELECT:
                        action = self.__action_queue.get()
                        key = KeyTranslator.get_key_value(action)
                        cmd = self.__match_command("", key)
                        if cmd not in self.__key_maps[self.__mode] or self.__key_maps[self.__mode][cmd] is None:
                            key_list = self.__get_key_action(action)
                            self.__press_key(*key_list)
                            continue
                        self.__key_maps[self.__mode][cmd]()
                        self.__timer.reset()
                        continue
                    if self.__mode == Mode.COMMAND:
                        cmd = self.__get_command()
                        if cmd in self.__key_maps[self.__mode] and self.__key_maps[self.__mode][cmd] is not None:
                            self.__key_maps[self.__mode][cmd]()
                        else:
                            self.__msg("command not found")
                        self.__timer.reset()
                        self.__mode = Mode.NORMAL
                        continue
                else:
                    self.__mode = Mode.INSERT
                    self.__keyboard_interceptor.pause()
                    self.__pressed_key_set.clear()
                continue

            # 在 Insert 模式下, 按下 Caps-Lock 后, 再次进入 Normal 模式
            if 20 in self.__stop_set:
                self.normal()
                self.__timer = Timer(self.__normal_timeout)
                self.__timer.start()
                self.__stop_set.clear()
                self.__keyboard_interceptor.goon()
                continue
            sleep(0.05)

    def do_mark(self):
        """
        在鼠标当前位置做标记
        """
        key = self.__action_queue.get()
        key_char = KeyTranslator.vk_2_char(key).upper()
        mark_name = self.__name[key_char]
        pos = SystemBase.get_position()
        self.__mark[mark_name] = pos

    def go_mark(self):
        """
        将鼠标移动到指定标记
        """
        key = self.__action_queue.get()
        key_char = KeyTranslator.vk_2_char(key).upper()
        mark_name = self.__name[key_char] if key_char in self.__name else None
        if mark_name is None:
            return
        pos = SystemBase.get_position()
        if mark_name is Name.RECENT:
            SystemBase.move_to(*self.__mark[mark_name])
            self.__mark[Name.RECENT] = pos
            return
        self.__mark[Name.RECENT] = pos
        SystemBase.move_to(*self.__mark[mark_name])

    def scroll_up(self):
        """
        滚轮向上滚动
        """
        self.__move_key_set.add(Action.SCROLL_UP)
        self.__move_signal.set()

    def scroll_down(self):
        """
        滚轮向下滚动
        """
        self.__move_key_set.add(Action.SCROLL_DOWN)
        self.__move_signal.set()

    def scroll_left(self):
        """
        滚轮向上滚动
        """
        self.__move_key_set.add(Action.SCROLL_LEFT)
        self.__move_signal.set()

    def scroll_right(self):
        """
        滚轮向下滚动
        """
        self.__move_key_set.add(Action.SCROLL_RIGHT)
        self.__move_signal.set()

    def move_down(self):
        """
        鼠标下移
        """
        self.__move_key_set.add(Action.MOVE_DOWN)
        self.__move_signal.set()

    def move_up(self):
        """
        鼠标上移
        """
        self.__move_key_set.add(Action.MOVE_UP)
        self.__move_signal.set()

    def move_left(self):
        """
        鼠标左移
        """
        self.__move_key_set.add(Action.MOVE_LEFT)
        self.__move_signal.set()

    def move_right(self):
        """
        鼠标右移
        """
        self.__move_key_set.add(Action.MOVE_RIGHT)
        self.__move_signal.set()

    def speed_max(self):
        """
        将移动速度调整到最大
        """
        self.__speed_record.max()

    def speed_min(self):
        """
        将移动速度调整到最小
        """
        self.__speed_record.min()

    def speed_down(self):
        """
        减小移动速度

        """
        self.__speed_record.speed_down()

    def stop(self):
        """
        退出 Vimouse
        """
        self.__toast.quit()
        self.__is_running = False

    def visual(self):
        """
        进入可视模式, 框选
        """
        if self.__mode != Mode.VISUAL:
            self.__mode = Mode.VISUAL
            SystemBase.mouse_down()
            return
        SystemBase.mouse_up()
        self.__mode = Mode.NORMAL

    def drag(self):
        """
        进入可视模式，拖动
        """
        if self.__mode != Mode.VISUAL:
            self.__mode = Mode.VISUAL
            SystemBase.mouse_down(btn="middle")
            return
        SystemBase.mouse_up("middle")
        self.__mode = Mode.NORMAL


    def insert(self):
        """
        进入插入模式
        """
        self.__mode = Mode.INSERT
        self.__keyboard_interceptor.pause()
        self.__pressed_key_set.clear()
        self.__timer.stop()

    def command(self):
        """
        进入命令模式
        """
        self.__mode = Mode.COMMAND
        self.__toast.show()

    def normal(self):
        """
        进入普通模式
        """
        self.__mode = Mode.NORMAL

    def insert_with_click(self):
        """
        点击左键并进入插入模式
        """
        self.__mode = Mode.INSERT
        self.click_left()
        self.__keyboard_interceptor.pause()
        self.__pressed_key_set.clear()
        self.__timer.stop()

    @classmethod
    def click_left(cls):
        """
        鼠标左键
        """
        SystemBase.click_left()

    def click_right(self):
        """
        鼠标右键
        """
        SystemBase.click_right()
        self.select_item()

    def task_toggle(self):
        """
        Windows 任务切换
        """
        self.__keyboard_interceptor.pause()
        SystemBase.key_down("alt")
        SystemBase.hotkey("tab")
        self.__stop_set.add(164)
        while 164 in self.__stop_set or 165 in self.__stop_set:
            sleep(0.1)
            continue
        SystemBase.key_up("alt")
        self.__timer = Timer(self.__normal_timeout)
        self.__timer.start()
        self.__stop_set.clear()
        self.__keyboard_interceptor.goon()

    def tab_toggle(self):
        """
        Windows Tab 切换
        """
        self.__keyboard_interceptor.pause()
        SystemBase.key_down("ctrl")
        SystemBase.hotkey("tab")
        self.__stop_set.add(162)
        while 162 in self.__stop_set or 163 in self.__stop_set:
            sleep(0.1)
            continue
        SystemBase.key_up("ctrl")
        self.__timer = Timer(self.__normal_timeout)
        self.__timer.start()
        self.__stop_set.clear()
        self.__keyboard_interceptor.goon()

    def window_menu(self):
        """
        打开窗口菜单
        """
        self.__press_key("alt", "space")
        self.select_item()

    def go_zero(self):
        """
        光标回到原点
        """
        SystemBase.move_to(0, 0)

    def go_center(self):
        """
        光标回到中心
        """
        width, height = SystemBase.get_screen_size()
        SystemBase.move_to(width / 2, height / 2)

    def go_end(self):
        """
        回到最大点
        """
        screen_width, screen_height = SystemBase.get_screen_size()
        SystemBase.move_to(screen_width, screen_height)

    def go_top(self):
        """
        回到顶部
        """
        width, height = SystemBase.get_position()
        SystemBase.move_to(x=width, y=self.__screen_height * 0.01)

    def go_middle(self):
        """
        回到中间
        """
        width, height = SystemBase.get_position()
        SystemBase.move_to(x=width, y=self.__screen_height / 2)

    def go_bottom(self):
        """
        回到底部
        """
        width, height = SystemBase.get_position()
        SystemBase.move_to(x=width, y=self.__screen_height * 0.99)

    def select_item(self):
        """
        用于在菜单中选择的模式
        """
        self.__mode = Mode.SELECT
        return

    def next(self):
        """
        下一个
        """
        self.__move_key_set.add(Action.NEXT)
        self.__move_signal.set()

    def previous(self):
        """
        上一个
        """
        self.__move_key_set.add(Action.PREVIOUS)
        self.__move_signal.set()

    def forward(self):
        """
        向前
        """
        self.__move_key_set.add(Action.FORWARD)
        self.__move_signal.set()

    def backward(self):
        """
        后退
        """
        self.__move_key_set.add(Action.BACKWARD)
        self.__move_signal.set()

    def confirm_select(self):
        """
        确认选项
        """
        self.__mode = Mode.NORMAL
        self.__press_key("enter")

    def quit_select(self):
        """
        退出选择模式
        """
        self.__mode = Mode.NORMAL

    def quit_select_with_esc(self):
        """
        退出选择模式, 并按下 ESC 键
        """
        self.__press_key("esc")
        self.__mode = Mode.NORMAL

    @classmethod
    def click_middle(cls):
        """
        鼠标中键
        """
        SystemBase.click_middle()

    def __get_key_action(self, action: Tuple[int, Tuple[int, int, int]]) -> list:
        """
        获得 key 的按键序列
        """
        if action is None:
            action = self.__action_queue.get()
        result = []
        if action[1][0]:
            result.append("ctrl")
        if action[1][1]:
            result.append("shift")
        if action[1][2]:
            result.append("alt")
        result.append(KeyTranslator.vk_2_char(action).lower())
        return result

    def __press_key(self, *keys: str, times: int = 1):
        self.__keyboard_interceptor.pause()
        SystemBase.hotkey(*keys, times=times)
        self.__keyboard_interceptor.goon()

    def __match_command(self, first: str, second: str) -> str:
        """
        通过递归的方式匹配按键映)射
        """
        temp = first + second
        pattern = re.compile('^"|\'' + temp)
        cmd_list = [cmd for cmd in self.__key_maps[self.__mode].keys()]
        result = pattern.findall(str(cmd_list))
        if len(result) > 1:
            key = KeyTranslator.get_key_value(self.__action_queue.get())
            return self.__match_command(temp, key)
        return temp

    def __get_command(self) -> str:
        """
        从用户输入获取命令
        """
        cmd = ""
        self.__toast.show()
        while True:
            key = self.__action_queue.get()
            key_char = KeyTranslator.vk_2_char(key)
            if key_char == "\r":
                self.__toast.send("")
                break
            if key_char == "\x08":
                cmd = cmd[0:len(cmd) - 1]
            else:
                cmd = cmd + key_char
            self.__toast.send(cmd)
        self.__toast.hide()
        return cmd

    @exec_in_thread
    def __msg(self, msg: str):
        """
        显示一条提示信息
        """
        self.__toast.show()
        self.__toast.send(msg)
        sleep(2)
        self.__toast.send("")
        self.__toast.hide()


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
    controller.join()
    lock.release()
    sys.exit()
