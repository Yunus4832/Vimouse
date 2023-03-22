from threading import Thread
from tkinter import *


class Toast(Thread):
    def __init__(self, width: int = 100, height: int = 100):
        super().__init__()
        self.alpha = 0.6
        self.bg = 'gray'
        self.fg = 'black'
        self.font = 'Consolas'
        self.message = ''
        self.lb = None
        self.tk = None
        self.geometry = None
        self.width = width
        self.height = height
        self.daemon = True

    def run(self):
        self.geometry = r'+' + str(self.width) + '+' + str(self.height)
        self.tk = Tk()
        self.lb = Label(self.tk, font=self.font, fg=self.fg, bg=self.bg)
        self.lb.pack()
        self.tk.geometry(self.geometry)
        self.tk.attributes('-alpha', self.alpha)
        self.tk.attributes('-topmost', True)
        self.tk.overrideredirect(True)
        self.tk.focus_get()
        self.tk.after(100, self.update)
        self.tk.mainloop()

    def update(self):
        message = " " + self.message + " "
        self.lb.config(text=message)
        self.lb.update()
        self.tk.after(100, self.update)

    def config(self, font=('Consolas', 18), fg='black', bg='gray', alpha=0.6):
        self.font = font
        self.fg = fg
        self.bg = bg
        self.alpha = alpha


# 测试模块
if __name__ == "__main__":
    print("GuiUtils Module")
