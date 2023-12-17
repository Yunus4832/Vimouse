import os
import portalocker

from functools import wraps
from threading import Thread, Semaphore
from time import sleep
from typing import Callable
from portalocker.exceptions import AlreadyLocked


def execInThread(func):
    """
    让方法在一个新线程中执行的修饰器
    """

    @wraps(func)
    def wrap(*args, **kwargs):
        Thread(target=func, args=args, kwargs=kwargs).start()

    return wrap


class FileLock:
    """
    文件锁，可以锁定一个系统文件 (filePath) 使其它进程无法访问该文件
    """

    def __init__(self, filePath: str):
        self.lockFilePath = filePath
        self.lockFile = open(self.lockFilePath, "w")

    def acquire(self) -> None:
        """
        请求文件锁
        """
        try:
            portalocker.lock(self.lockFile, portalocker.LOCK_EX | portalocker.LOCK_NB)
        except AlreadyLocked:
            raise RuntimeError("该文件已被其他进程锁定。")

    def release(self) -> None:
        """
        释放文件锁，同时删除临时文件
        """
        self.lockFile.close()
        os.remove(self.lockFilePath)


class Timer(Thread):
    """
    计时器
    """

    def __init__(self, timeout: int = 60):
        super(Timer, self).__init__()
        self.__timerSemaphore = Semaphore(1)
        self.__timeout = timeout
        self.__count = timeout
        self.__isRunning = True
        self.__func = None
        self.__args = None
        self.__kwargs = None
        self.name = "Timer"
        self.daemon = True

    def run(self):
        while self.__isRunning:
            if self.__count <= 0:
                break
            self.__timerSemaphore.acquire()
            self.__count -= 1
            self.__timerSemaphore.release()
            sleep(1)
        self.__isRunning = False
        if self.__func is not None:
            self.__func(*self.__args, **self.__kwargs)

    def setFunc(self, func: Callable, *args: any, **kwargs: any) -> None:
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

    def config(self, timout: int) -> None:
        self.__timeout = timout
        self.__count = self.__timeout

    def reset(self) -> None:
        self.__timerSemaphore.acquire()
        self.__count = self.__timeout
        self.__timerSemaphore.release()

    def isRun(self) -> bool:
        return self.__isRunning

    def stop(self) -> None:
        self.__isRunning = False


if __name__ == "__main__":
    print("CommonUtils Module")
