from threading import Thread
from tkinter import *


# 桌面提示 Toast
class Toast(Thread):
    def __init__(self, positionX: int = 0, positionY: int = 0, width: int = 100, height: int = 100):
        super().__init__()
        self.alpha = 0.6
        self.bg = 'gray'
        self.fg = 'black'
        self.font = 'Consolas'
        self.prefix = ':'
        self.positionX = positionX
        self.positionY = positionY
        self.width = width
        self.height = height
        self.lb = None
        self.tk = None
        self.geometry = None
        self.name = "Toast"

    def run(self):
        self.geometry = r'' + str(self.width) + 'x' + str(self.height) + \
                        '+' + str(self.positionX) + '+' + str(self.positionY)
        self.tk = Tk()
        self.lb = Label(self.tk, font=self.font, fg=self.fg, bg=self.bg)
        self.lb.config(text=self.prefix)
        self.lb.place(x=10, y=0)
        self.tk.geometry(self.geometry)
        self.tk.configure(background=self.bg)
        self.tk.attributes('-alpha', self.alpha)
        self.tk.attributes('-topmost', True)
        self.tk.overrideredirect(True)
        self.tk.focus_get()
        self.hide()
        self.tk.mainloop()

    def config(self, font=('Consolas', 18), fg='black', bg='gray', alpha=0.6):
        """
        配置字体, 颜色, 透明度
        """
        self.font = font
        self.fg = fg
        self.bg = bg
        self.alpha = alpha

    def send(self, msg: str):
        """
        发送消息
        """
        self.lb.config(text=self.prefix + msg)

    def __destroy(self):
        """
        销毁窗口
        """
        self.tk.destroy()

    def quit(self):
        """
        退出 tk 窗口
        """
        self.tk.after(0, self.__destroy)

    def hide(self):
        """
        隐藏窗口
        """
        self.tk.withdraw()

    def show(self):
        """
        显示窗口
        """
        self.tk.deiconify()


if __name__ == "__main__":
    print("GuiUtils Module")
