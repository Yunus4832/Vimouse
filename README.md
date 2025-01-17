重构 Vimouse
------
[参考项目: https://github.com/firemakergk/vimouse](https://github.com/firemakergk/vimouse)

Vimouse 希望能够像 vim 编辑器一样操作鼠标。 
我修改并使用了一段时间由 firemakergk 开源的 Vimouse，firemakergk 的 Vimouse 很棒，可以使用 vim 中移动光标的方式移动鼠标，使用特殊的按键组合实现不同的移动速度，并且可以模拟鼠标的点击，鼠标移动流畅，并且使用 PyQt 实现了一个可配置的用户界面。
但是该项目有一些不足之处，例如 只支持了 Vim 中少量的操作，图形配置界面可配置内容较少，并且我并不需要图形界面进行配置，由于图形库的加入，打包体积也变得庞大。
有些按键映射和 vim 有所冲突等。

于是我参考 Vimouse 的源码，重构了一个更符合我自身需求的 Vimouse, 它更加强大小巧，并且也更易于扩展，感谢 firemakergk 提供的创意和灵感 ^_^

## 1、 打包 & 安装

可以使用如下流程将 Vimouse 代码打包成单个可执行文件, Vimouse 使用 Python 实现，因此在进行操作前，系统应已经有可用的 Python 环境。

```bat
REM 克隆项目
git clone https://github.com/Yunus4832/Vimouse.git
REM 进入工作目录
cd Vimouse
REM 创建 Python 虚拟环境
python -m venv venv
REM 激活虚拟环境
.\venv\Scripts\active.bat
REM 安装依赖
pip install -r requirements.txt
REM 执行打包命令
.\build.bat
```

## 2、如何使用

以下仅列举出以实现的功能，这些功能往往是在操作鼠标时提供效率所需要的，这些功能大部分来自于 Vim 中的操作习惯，并且其中大部分映射是可配置的。

- **启动**， 运行程序后 Vimouse 默认使用插入模式，不监听按键，使用 `caps lock` 切换到普通模式，使用它是因为我本人觉得 该键作用不大，并且我没有找到合适的按键，注意该键不可配置，如果需要切换大写锁定，需要按键 `caps lock` 两次, 如需修改则需要修改代码重新打包。

- **标记**，使用 `m` 触发 标记(mark)，Vimouse 会把鼠标当前所在位置记录在标签中，使用 `'` 或者 `` ` `` 将跳转到相应标签。

- **移动**，使用 `j` `k` `h` `l` 进行鼠标的移动，使用 `gc` 跳转到屏幕中心，`gg` 跳转到屏幕零点。`zz` 跳转到屏幕水平中央，`zt` 跳转到屏幕顶端，`zb` 跳转到屏幕底部。类似 Vim。

- **翻页/滚动**，使用 `ctrl-b` `ctrl-f` 或者 `alt-j` `alt-k` 进行翻页或者鼠标滚轮的滚动功能。

- **点击**，使用 `entry` 键点击鼠标左键，使用 `alt-entry` 组合键点击鼠标右键, 注意，鼠标右键会自动进入选择模式，见下选择模式说明，使用 `ctrl-entry` 组合键表示点击鼠标中键，这样配置是考虑到不同按键使用的频率不同。
 
- **速度调节**，使用 `a` 调节鼠标的移速，在 Vimouse 中这设置了三档速度，它们分别是 2<sup>5</sup>，2<sup>3</sup>， 2<sup>1</sup> 个单位。
  这样设计是考虑到鼠标移动定位的过程是由快到慢的，并且其速度变化类似指数变化，这样能使得鼠标定位过程更加平滑，`a` 键会在三个移动速度间切换，由于只有三档的速度，在不同挡位切换比较轻松。
  也可以使用 `alt-a` 将移动速度调整到最大，使用 `ctrl-a` 将移动速度调整到最小。

- **插入**, 使用 `i` 键暂时回到普通输入模式, 使用 `caps lock` 回到普通模式, 使用 `i` 命令进入普通输入模式不会点击鼠标当前位置。
  如果需要进入输入模式前先点击鼠标所在位置，可以使用 `shift-i` 这在点击需要在输入框中输入内容时可能很有用，因为这时会自动点击输入框，窗口焦点也自然聚焦到输入框。

- **可视**, 使用 `v` 键进入可视模式，该模式下继续移动指针，再次按下 `v` 键，两次按下的位置形成的矩形框中的内容将被选中, 类似点击鼠标不放开拖动选择内容, 可视模式下，并不影响其他移动鼠标的命令发挥作用。

- **选择**, 使用 `s` 可以进入选择模式，该模式需要额外说明，在 vim 中并没有对应的模式叫做选择模式，该模式希望解决菜单或目录难以选中的问题。
  原理十分简单，该模式只做了最简单的按键映射，`j -> down`, `k -> up`, `h -> left`, `l -> right`, `enter` 确认选择并回到 Normal 模式, `shift-q` 命令用于退出选择模式并回到 Normal 模式，`q` 命令用于退出选择模式，并自动按下 `esc` 键。有了这些映射，在需要使用键盘上方向键进行选择的场景都可以使用选择模式。
  一个典型的应用场景时鼠标右键点击弹出的菜单，因此，在 Vimouse 中，右键点击会自动进入该模式，此时可以使用 `j` `k` `h` `l` 选择菜单或者子菜单，并使用 `enter` 确认菜单中的选择。

- **退出**, 如果想要退出 Vimouse, 需要进入命令模式，然后执行退出命令, 即 `:q`, 同 vim, 目前命令模式只支持退出命令

## 3、配置

开发中......

## 4、原理

更新中......

## 5、 Q & A

更新中......
