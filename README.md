# Manjaro XFCE 终端配置包

将这套 **Starship 提示符 + zsh 命令高亮 + fzf 搜索 + tmux 分屏与监控** 迁移到另一台电脑。

> **适用环境：x86_64 架构的 Manjaro XFCE。** 在目标电脑的图形桌面终端中操作。安装脚本使用普通用户运行，会先备份原配置。

## 目录

- [1. 安装后有哪些功能](#1-安装后有哪些功能)
- [2. 完整安装步骤](#2-完整安装步骤)
- [3. VS Code 终端](#3-vs-code-终端)
- [4. tmux 使用与快捷键](#4-tmux-使用与快捷键)
- [5. fzf 搜索与快捷键](#5-fzf-搜索与快捷键)
- [6. 外观与顶部监控](#6-外观与顶部监控)
- [7. 常见问题](#7-常见问题)
- [8. 配置文件与备份恢复](#8-配置文件与备份恢复)
- [9. 适用范围与验证情况](#9-适用范围与验证情况)

## 1. 安装后有哪些功能

| 组件 | 功能 |
| --- | --- |
| zsh | 命令自动建议、语法高亮，已识别命令显示灰薄荷绿 |
| Starship | 基于 Jetpack 定制；显示目录、Git 分支、项目版本、语言版本和时间 |
| fzf | 模糊搜索历史命令、文件和目录 |
| tmux | work 会话、多窗口、左右/上下分屏、组合键切换 |
| 顶部监控 | CPU、内存、网络上传/下载和历史曲线，占三行 |
| 字体 | MesloLGS NF，支持提示符图标 |
| XFCE 终端 | 默认 120 列 × 24 行、透明背景、隐藏菜单栏/边框/滚动条 |

**不包含**桌面壁纸、任务栏透明度、显示器布局、VS Code 主题和扩展，也不复制个人命令历史、密码或项目文件。

## 2. 完整安装步骤

### 第一步：克隆仓库

在另一台 Manjaro 电脑上打开终端。如果没有 Git，先安装：

```bash
sudo pacman -Syu --needed git
```

克隆并进入仓库（下面以用户主目录为例）：

```bash
cd ~
git clone https://github.com/jingpengju391/manjaro-terminal-kit.git
cd manjaro-terminal-kit
```

**后面的安装命令都在仓库目录内执行**，因此使用 `bash install.sh`，不要再重复加 `manjaro-terminal-kit/`。如果仓库需要身份验证，请使用有访问权限的 GitHub 账号。

如果已经克隆过，不要重复克隆，参照下方“后续更新”。如果你放在其他目录，请将 `~/manjaro-terminal-kit` 替换为实际路径。

### 第二步：安装系统依赖

如果目标电脑已装齐依赖，可以直接进入下一步。否则执行：

```bash
sudo pacman -Syu --needed zsh manjaro-zsh-config zsh-autosuggestions zsh-syntax-highlighting xfce4-terminal python fontconfig python-gobject gtk3
```

依赖安装需要网络和管理员密码。主题、字体、Starship、fzf 和 tmux 已打包，不需要再次下载。

> `sudo` 只用于上面的系统依赖安装。**不要执行 `sudo bash install.sh`**，否则会把配置安装给错误的用户，脚本也会拒绝运行。

### 第三步：检查环境

```bash
bash install.sh --check
```

显示“环境检查通过；未修改任何配置”后继续。缺少依赖时按提示安装；如果提示无法访问 XFCE 配置，请在目标电脑已登录的图形桌面中运行，并先打开一次 XFCE Terminal。

### 第四步：安装配置

```bash
bash install.sh
```

安装会备份并替换现有 `.zshrc`、`.tmux.conf`、Starship 配置和同名用户工具，设置字体及 XFCE 终端外观。**已有 alias、NVM 等个人初始化不会自动合并**，需要从备份中按需取回。

安装末尾会显示备份目录和完整回滚命令，建议保留这段输出。

已安装 Git 和系统依赖、且尚未克隆仓库时，也可以连续执行：

```bash
cd ~
git clone https://github.com/jingpengju391/manjaro-terminal-kit.git && cd manjaro-terminal-kit && bash install.sh
```

### 第五步：启用 zsh

将 zsh 设置为今后的默认登录 shell：

```bash
chsh -s /usr/bin/zsh
```

输入用户密码，然后**注销桌面并重新登录**。如果只想先在当前终端体验，执行：

```bash
exec zsh
```

`exec zsh` 只替换当前 shell，不会永久更改默认登录 shell。请在命令执行结束、回到提示符时操作。

### 第六步：试用

1. 输入 `cd` 或 `clear`，观察灰薄荷绿命令高亮。
2. 按 `Ctrl+T`，进入名为 `work` 的 tmux 会话。
3. 按 `Ctrl+N` 新建一个窗口。
4. 按 `Ctrl+左/右` 切换窗口。
5. 按 `Ctrl+反斜杠` 创建左右分屏，再用 `Alt+方向键` 切换。
6. 按 `Ctrl+R` 搜索历史命令。

### 后续更新

进入此前克隆的仓库，拉取远程更新后重新应用配置：

```bash
cd ~/manjaro-terminal-kit
git pull --ff-only
bash install.sh --check
bash install.sh
```

**`git pull` 只更新仓库文件，不会自动更新正在使用的终端配置。** 安装前检查 `git pull` 和 `--check` 是否成功；若失败，先解决报错，不要继续安装。每次安装都会生成一份新备份；重新安装会覆盖相关个人配置，先保存自己的定制。

只更新原生终端外观时，最后一条改为：

```bash
bash install.sh --terminal-only
```

需要同时更新 VS Code 终端设置时，最后一条改为：

```bash
bash install.sh --vscode
```

如果 `git pull --ff-only` 提示本地改动或分支分叉，请先查看 `git status` 并保留自己的修改，不要直接执行强制重置。更新后新开终端；已有 tmux 分屏的 zsh 配置可在空闲提示符处用 `exec zsh` 重新加载。

## 3. VS Code 终端

### 自动配置

如果还没安装，第四步可以改用：

```bash
bash install.sh --vscode
```

这个选项会合并以下设置：

- 终端字体：`MesloLGS NF`。
- Linux 默认终端：`zsh`。
- 添加或更新名为 `zsh` 的终端配置。

它不会安装 VS Code，也不会更换编辑器主题或隐藏 VS Code 滚动条。

### 手动配置

如果 `settings.json` 有注释或尾逗号，自动配置会在修改前停止。可以不带 `--vscode` 安装，再在 VS Code 设置中搜索并设置：

| 设置项 | 值 |
| --- | --- |
| `terminal.integrated.fontFamily` | `MesloLGS NF` |
| `terminal.integrated.defaultProfile.linux` | `zsh` |

关闭旧的集成终端并新建终端。如果字体仍没更新，重新启动 VS Code。

> VS Code 自身可能占用 `Ctrl+T`、`Ctrl+N` 或 `Alt+方向键`。这些 tmux 组合键只有传到终端才会生效；有冲突时在 VS Code 键盘快捷方式中调整对应绑定，或使用下文的 tmux 前缀快捷键。

## 4. tmux 使用与快捷键

### 会话、窗口和分屏有什么区别

| 名称 | 可以理解为 | 示例 |
| --- | --- | --- |
| 会话（session） | 一个工作空间 | `work` |
| 窗口（window） | 工作空间里的标签页 | 底部的 `1:zsh`、`2:zsh`、`3:zsh` |
| 分屏（pane） | 同一窗口里并排显示的终端 | 左边写代码，右边运行命令 |

`Ctrl+N` 增加底部窗口编号；`Ctrl+反斜杠` 或 `Ctrl+减号` 则切分当前窗口。

### 不需要前缀的组合键

| 快捷键 | 功能 | 生效位置 |
| --- | --- | --- |
| `Ctrl+T` | 创建或恢复 `work` 会话 | zsh 命令行提示符处 |
| `Ctrl+N` | 新建窗口，沿用当前目录 | tmux 内 |
| `Ctrl+Y` | 关闭当前窗口，按 `y` 确认 | tmux 内；会关闭该窗口全部分屏及程序 |
| `Ctrl+←` | 切到上一个窗口 | tmux 内 |
| `Ctrl+→` | 切到下一个窗口 | tmux 内 |
| `Ctrl+\` | 左右分屏 | tmux 内 |
| `Ctrl+-` | 上下分屏 | tmux 内 |
| `Alt+←/→/↑/↓` | 切到对应方向的分屏 | tmux 内 |
| 鼠标单击 | 选择分屏 | tmux 内 |
| 鼠标拖动分隔线 | 调整工作分屏大小 | tmux 内 |

`Ctrl+\` 是按住 Ctrl 再按反斜杠键，不需要 Shift。拆分前请先选中工作分屏，不要选顶部监控栏。

### 使用 Ctrl+B 前缀的快捷键

**操作顺序：按 `Ctrl+B` → 松开两个键 → 再按表格中的键。** 不是三个键同时按。

| 前缀后按 | 功能 | 说明 |
| --- | --- | --- |
| `c` | 新建窗口 | `Ctrl+N` 的替代方式 |
| `n` / `p` | 下一个 / 上一个窗口 | Ctrl 方向键冲突时可用 |
| `1`、`2`、`3`… | 跳到对应编号窗口 | 例如 `Ctrl+B` 后按 `2` |
| `w` | 打开窗口列表 | 方向键选择，Enter 确认 |
| `\` | 左右分屏 | 备用分屏方式 |
| `-` | 上下分屏 | 备用分屏方式 |
| 方向键 | 切换分屏 | Alt 方向键冲突时可用 |
| `z` | 放大当前分屏 / 恢复布局 | 放大期间顶部监控也会隐藏 |
| `d` | 离开会话，返回外层终端 | 会话和程序仍在后台运行 |
| `x` | 关闭当前分屏 | 出现确认后按 `y`；会终止其中的程序 |
| `&` | 关闭当前窗口及其分屏 | 出现确认后按 `y`；会终止其中的程序 |
| `,` | 重命名当前窗口 | 输入名称后 Enter |
| `[` | 进入滚动/复制模式 | 方向键或 PageUp/PageDown 滚动，按 `q` 退出 |
| `r` | 重新加载 tmux 配置 | 不会重新加载已有分屏的 `.zshrc` |

### 离开、重新进入与关闭

- **暂时离开**：`Ctrl+B` 后按 `d`，程序继续运行。
- **回来继续**：在 zsh 提示符处按 `Ctrl+T`，恢复原来的窗口和分屏。
- **关闭一个工作分屏**：在空闲 shell 中输入 `exit`，或用 `Ctrl+B` 后按 `x`。
- **关闭整个窗口**：按 `Ctrl+Y`，再按 `y` 确认（也可用 `Ctrl+B` 后按 `&`）。关闭后窗口会自动重新编号。

查看会话也可以使用命令：

```bash
tmux list-sessions
```

> tmux 保留的是当前开机期间的会话。它不会在重启电脑后恢复原来正在运行的程序；重启后第一次按 `Ctrl+T` 会新建 work，并自动显示监控栏。

## 5. fzf 搜索与快捷键

在 zsh 的命令行提示符处使用，正在运行的编辑器或其他程序可能自行处理这些按键。

| 快捷键 | 功能 | 选中后的行为 |
| --- | --- | --- |
| `Ctrl+R` | 模糊搜索命令历史 | 将命令放回输入行，再按 Enter 执行 |
| `Alt+T` | 模糊搜索文件/路径 | 将选中的路径插入当前命令行 |
| `Alt+C` | 模糊搜索目录 | 进入选中的目录 |
| `↑` / `↓` | 在搜索结果中移动 | 选择候选项 |
| `Enter` | 确认选择 | 行为取决于使用的搜索功能 |
| `Esc` | 取消搜索 | 返回命令行 |

本配置将 fzf 原来的 `Ctrl+T` 文件搜索移到了 **`Alt+T`**，因为 `Ctrl+T` 已用于进入 tmux。

### 两个例子

**找以前执行过的命令：** 按 `Ctrl+R`，输入 `cargo`，选中一条历史命令后按 Enter。检查命令内容，再按 Enter 执行。

**为命令补上文件路径：** 先输入 `cat `（后面有空格），按 `Alt+T` 搜索文件并确认，路径就会插入到 `cat` 后面。

搜索结果与当前目录、已有历史记录有关。新电脑没有复制旧历史，`Ctrl+R` 一开始内容很少是正常的。

## 6. 外观与顶部监控

### 当前外观

| 项目 | 设置 |
| --- | --- |
| 字体 | MesloLGS NF 10 |
| 新窗口尺寸 | 120 列 × 24 行，可自由拖动改变 |
| 命令及成功提示符颜色 | 灰薄荷绿 `#9BC8AC` |
| XFCE 终端背景 | 透明模式，背景深度参数 `0.75` |
| 菜单栏 / 窗口边框 / 滚动条 | 默认隐藏 |
| Starship 信息 | 根据当前目录和项目自动显示 |

透明背景需要在 **窗口管理器微调 → 合成器** 中启用显示合成。背景下方如果有应用窗口，会透出应用内容；它不是只显示桌面壁纸的背景图。

隐藏窗口边框后，XFCE 常见操作是按住 Alt 并用鼠标左键拖动窗口；实际行为取决于目标电脑的窗口管理器配置。右键终端可进入偏好设置，恢复菜单或其他选项。

### 监控栏内容

| 指标 | 含义 |
| --- | --- |
| CPU | 当前 CPU 使用率 |
| RAM | 已用内存 / 总内存 |
| `↓` | 默认路由网卡的下载速率 |
| `↑` | 默认路由网卡的上传速率 |
| 小曲线 | 近期采样变化；刚启动时需逐步积累数据 |
| 日期时间 | 当前本地时间 |

监控约每秒采样一次。顶部监控是一个专用 tmux 分屏，占三行，窗口缩放后会重新校正高度。窄窗口会精简内容；放大工作分屏时会暂时隐藏监控。底部显示 work 和各窗口编号。

## 7. 常见问题

### 绿色还是原来的荧光绿

旧 tmux 分屏中的 zsh 进程还在使用旧配置。在**每个需要更新的空闲分屏**里分别执行：

```bash
exec zsh
```

新建分屏会自动加载新颜色。仅仅重新打开外层终端、再进入旧 work，不会更新旧 shell。

### 图标显示方框或不对齐

先确认终端字体为 `MesloLGS NF`，再刷新字体缓存：

```bash
fc-cache -f
fc-match 'MesloLGS NF'
```

重新打开终端。VS Code 需要单独设置终端字体，见第三节。

### 没有 Git 分支或 Rust 版本

分支信息只会在 Git 仓库目录中出现；语言和项目版本也取决于当前项目文件及已安装的工具。先 `cd` 到实际项目目录再观察。窗口太窄时，右侧提示符可能没有足够空间显示。

### 为什么每次进入 work 都有原来的分屏

`Ctrl+T` 的作用是恢复已有会话，因此会保留已有布局。这不是每次都新建一套分屏。关闭不需要的工作分屏，或者按 `Ctrl+N` 新建窗口即可。

### 顶部监控消失或高度异常

先检查是否用了分屏放大：`Ctrl+B` 后按 `z` 恢复。然后重新加载配置：

```bash
~/.local/bin/tmux source-file ~/.tmux.conf
```

切换一次窗口，或等待几秒让监控检查运行。顶部监控不要用于输入命令，使用下方工作分屏。

### Ctrl+T、Ctrl+N 或方向组合键没反应

确认当前使用 zsh、已进入 tmux（除 Ctrl+T 外），并检查桌面或 VS Code 有没有拦截这些按键。可以先在独立 XFCE Terminal 测试，再用第四节的前缀快捷键作为替代。

### 透明效果和原电脑不完全一样

透明效果受合成器、壁纸、背后窗口、GTK 主题和字体渲染影响。本包不会修改全局桌面主题和任务栏，因此不保证两台电脑的整个桌面完全相同。

### 安装出现校验失败

`install.sh` 会校验包内文件。先用 `git status --short` 检查仓库文件是否被改动，再用 `git pull --ff-only` 获取完整更新；手动编辑仓库内文件也会导致校验失败。不要为了通过校验直接丢弃未保存的修改。安装后需要定制时，请修改用户目录里的配置文件。

## 8. 配置文件与备份恢复

### 安装位置

| 路径 | 用途 |
| --- | --- |
| `~/.zshrc` | shell 初始化、命令高亮、fzf 与 Ctrl+T |
| `~/.config/starship.toml` | 提示符外观和模块 |
| `~/.tmux.conf` | tmux 快捷键、状态栏和监控钩子 |
| `~/.local/bin/` | Starship、fzf、tmux 可执行文件 |
| `~/.local/libexec/tmux-monitor.py` | 监控数据与曲线绘制 |
| `~/.local/libexec/tmux-monitor-window.py` | 监控分屏创建、恢复与高度调整 |
| `~/.local/share/fonts/terminal-kit/` | 字体 |
| XFCE 的 `xfce4-terminal` 配置通道 | 透明度、默认尺寸、菜单和滚动条等 |
| `~/.config/Code/User/settings.json` | 仅 `--vscode` 时修改 |

### 恢复安装前的配置

每次安装都会创建独立备份目录：

```text
~/.local/state/manjaro-terminal-kit/时间戳/
├── files/          原文件备份
├── manifest.json   本次修改记录
└── restore.py      本次回滚脚本
```

查看已有备份：

```bash
ls -1 ~/.local/state/manjaro-terminal-kit/
```

然后使用**安装完成时输出的完整回滚命令**，或将下面的 `实际时间戳` 替换为对应目录名：

```bash
python3 ~/.local/state/manjaro-terminal-kit/实际时间戳/restore.py
```

恢复后重新打开终端。回滚会覆盖安装后对相关配置的修改，先保存想保留的内容；它不会终止已运行的 tmux 程序，也不会恢复通过 `chsh` 手动修改的登录 shell。

重复安装时，最新备份保存的是“最近一次安装之前”的状态；要恢复最初的配置，应找到第一次安装的备份。

## 9. 适用范围与验证情况

- 包内工具版本：Starship **1.26.0**、fzf **0.74.5**、tmux **3.7c**。
- 面向 **x86_64 Manjaro XFCE**；ARM、Windows、GNOME/KDE 不在本包自动安装范围内。
- 包内校验、本机只读依赖检查、Python/zsh/Bash 语法和 Starship TOML 解析已检查。
- 尚未在另一台全新 Manjaro 电脑上完成端到端安装验证。
- 第三方许可保存在 `licenses/`，各组件保留原作者版权。

### Ctrl+- 被终端拦截时

部分终端将 `Ctrl+-` 用于缩小字体，需要先在终端快捷键设置中解除冲突。本配置也支持传统编码 `Ctrl+_`（通常为 `Ctrl+Shift+-`）进行上下分屏；备用操作仍是 `Ctrl+B` 松开后按 `-`。

### 分屏内直接拖选复制

在工作分屏内直接按住鼠标左键拖选，松开即复制到系统剪贴板，并保留选区高亮；按 `Esc` 退出选择模式，继续输入命令。**不用 Shift，也不用 Ctrl+Shift+C**，选择不会跨到相邻分屏。粘贴仍用 `Ctrl+Shift+V`。此功能依赖 X11、python-gobject 和 GTK 3；一个后台辅助进程持有最近复制的内容，剪贴板被替换后退出。

鼠标拖选优先由 tmux 处理，即使分屏内应用启用了鼠标模式，也会进入 tmux 文本选择。选择完成后按 `Esc` 返回应用。

选中文字显示蓝底白字，松开鼠标会复制并保留选区；按 `Esc` 返回命令行。

若能复制但拖动时没有高亮，检查 `copy-mode-selection-style`。本配置为 tmux 3.7 显式指定蓝底白字，不仅设置 `mode-style`。

### 检查时出现 GLIBC_x.xx not found / Python ImportError

如果报错指向 `/usr/lib/python3.x/lib-dynload/math...so` 和 `/usr/lib/libm.so.6`，这是目标电脑的系统 Python 与 glibc 不匹配，而非主题配置错误。常见原因包括部分升级或混用软件源，不能仅凭该报错确定具体来源。

在目标电脑运行完整升级并重装匹配的软件包（会升级系统软件）：

```bash
sudo pacman -Syu glibc python
```

成功后重启，再检查：

```bash
python3 -c 'import math; print("Python OK")'
cd ~/manjaro-terminal-kit
bash install.sh --check
```

若升级失败，保留完整 pacman 输出，不要手动复制/替换 libm.so.6 或 libc.so.6。若升级成功但错误仍在，请提供 `pacman -Q glibc python`、`type -a python3` 和 `ldd --version` 的输出，以排查混源、环境变量或包文件异常。

依据：[Manjaro Pacman 官方说明](https://wiki.manjaro.org/index.php?title=Pacman_Overview/en)。

## 单独应用原生 XFCE 终端外观

`--check` **只检查环境，不修改任何外观**。完整安装本来就包含终端设置；也可以只应用终端外观：

```bash
bash install.sh --terminal-only
```

应用的项目：隐藏标题栏及窗口边框、菜单栏、工具栏和滚动条；默认窗口 120 列 × 24 行；透明背景深度 0.75；字体 MesloLGS NF 10。该选项不安装字体或修改 zsh/tmux，字体需先通过完整安装获得。

安装器识别 XFCE Terminal 版本：1.1 及以上通过 xfconf 设置，旧版写入 terminalrc。修改前均备份，可用该次生成的 restore.py 恢复。

旧窗口可能保留创建时的标题栏/菜单状态。请新开一个窗口验证：

```bash
xfce4-terminal --disable-server --hide-menubar --hide-toolbar --hide-borders
```

不要为了刷新外观强制关闭有任务的终端。透明效果依赖 XFCE 合成器；这些设置只适用于 XFCE Terminal，不会隐藏 VS Code 的应用标题栏。
