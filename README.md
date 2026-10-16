# Manjaro 终端配置包（KDE Plasma / Xfce / GNOME）

将这套 **Starship 提示符 + zsh 命令高亮 + fzf 搜索 + tmux 分屏与监控** 迁移到另一台电脑。

> **适用环境：x86_64 架构的 Manjaro，KDE Plasma / Xfce / GNOME 桌面。具体能力以实际终端为准。** 在目标电脑的图形桌面终端中操作。安装脚本使用普通用户运行，会先备份原配置。

## 先确认桌面与终端

安装器先读取 `XDG_CURRENT_DESKTOP` / `DESKTOP_SESSION` 和 X11/Wayland 信息，再检查对应终端是否安装，并打印所选目标。自动选择的是桌面常用终端，不是猜测当前 tmux 外层应用；使用其他终端时务必用 `--terminal` 指定。

| 桌面 | 自动选择 | 配置方式 |
| --- | --- | --- |
| KDE Plasma | Konsole（21.12+） | `konsolerc` + 独立 Terminal Kit profile/colorscheme |
| Xfce | XFCE Terminal | 1.1+ 用 xfconf；旧版用 terminalrc |
| GNOME | GNOME Terminal | 默认 profile 的 GSettings/dconf |

默认安装会为 GNOME 补装 GNOME Terminal；只检查时若仅有 Ptyxis 或 GNOME Console（kgx），会提示缺少支持的终端，**不会把它们当作 GNOME Terminal**。未知桌面或无法识别目标时要求显式选择，不会盲写 XFCE 配置。

| 外观项目 | Konsole | XFCE Terminal | GNOME Terminal |
| --- | --- | --- | --- |
| 隐藏标题栏/边框 | 写入应用自身无边框选项 | 支持 | 没有通用支持，明确提示未配置 |
| 菜单栏 | 默认配置及启动参数 | 支持 | 启动参数隐藏；新版全局键可能已弃用 |
| 工具栏 | 配置及支持时的启动参数 | 支持 | Headerbar 可关闭，但不等于无标题栏 |
| 滚动条 | 隐藏 | 隐藏 | 隐藏 |
| 背景透明 | 75% 不透明度，依赖合成器 | 背景深度 0.75，依赖合成器 | 仅发行版存在透明度扩展键时配置；标准版不支持 |
| 默认尺寸 | 120×24，关闭记忆旧窗口大小 | 120×24 | 120×24 |

**“写入成功”不等于正在打开的窗口已经更新。** 安装器生成 `~/.local/bin/terminal-kit`，用它打开新窗口查看；不会强制关闭已有任务。

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
| 原生终端外观 | 按检测到的终端设置字体、尺寸、滚动条等；透明度及无边框支持见上表 |

**不包含**桌面壁纸、任务栏透明度、显示器布局、VS Code 主题和扩展，也不复制个人命令历史、密码或项目文件。

## 2. 完整安装步骤

### 新电脑：克隆后运行一条安装命令

在目标电脑已登录的图形桌面中打开终端：

```bash
git clone https://github.com/jingpengju391/manjaro-terminal-kit.git
cd manjaro-terminal-kit
bash install.sh
```

**不需要自己判断 KDE / Xfce / GNOME，也不需要填写 `--terminal`。** 安装器会：

1. 自动识别桌面和 X11 / Wayland，选择对应终端。
2. 检查依赖，缺少时调用 `sudo pacman -Syu --needed` 补齐。系统会要求密码及确认；该操作包含系统完整升级，取消即停止安装。
3. 检查终端配置接口，在修改用户配置前生成备份。
4. 应用对应终端外观、字体、Starship、fzf、tmux 和快捷键。
5. 创建应用菜单中的 **Terminal Kit**，打开即可进入配置好的 zsh。

如果没有 Git，先运行 `sudo pacman -Syu --needed git`。如果仓库要求身份验证，请使用有访问权限的 GitHub 账号。**不要执行 `sudo bash install.sh`**。

安装结束后，从应用菜单打开 **Terminal Kit**，或者运行：

```bash
~/.local/bin/terminal-kit
```

在新窗口按 `Ctrl+T` 进入 work，按 `Ctrl+N` 新建窗口，按 `Ctrl+左/右` 切换窗口。按 `Ctrl+反斜杠` 左右分屏，按 `Alt+方向键` 切换分屏。

这个入口会直接启动 zsh，无须更改账户默认 shell。若希望其他终端入口也默认使用 zsh，可选执行 `chsh -s /usr/bin/zsh`，然后注销并重新登录。

> 安装会备份并替换现有 `.zshrc`、`.tmux.conf`、Starship 配置和同名用户工具。已有 alias、NVM 等个人初始化不会自动合并，可从备份中取回。安装末尾显示备份位置和恢复命令。系统包升级不属于配置备份的恢复范围。

### 可选：只检查，不安装

```bash
bash install.sh --check
```

该命令不安装依赖、不写入配置，也不生成备份。普通迁移不需要单独运行它；默认安装自带检查。Python/GLIBC 损坏时会停止并给出修复提示，不会强行替换系统库。

自动选择 KDE 的 Konsole、Xfce 的 XFCE Terminal、GNOME 的 GNOME Terminal；缺少对应终端时会安装。GNOME 的 Ptyxis/Console 不会被修改。未知桌面或使用其他终端时，才需要手动指定 `--terminal`，详见文末高级用法。不同终端的能力限制仍以开头表格为准。

### 后续更新

进入此前克隆的仓库，拉取远程更新后重新应用配置：

```bash
cd ~/manjaro-terminal-kit
git pull --ff-only && bash install.sh
```

**`git pull` 只更新仓库文件，不会自动更新正在使用的终端配置。** 更新成功后安装器自动检查环境；检查失败会停止。每次安装都会生成一份新备份；重新安装会覆盖相关个人配置，先保存自己的定制。

只更新原生终端外观及字体时，最后一条改为：

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

如果还没安装，安装命令可以改用：

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
| 终端背景 | Konsole / XFCE 为 75% 不透明度；GNOME 取决于是否提供透明度扩展 |
| 菜单栏 / 工具栏 / 窗口边框 / 滚动条 | 按终端能力隐藏，限制见开头对照表 |
| Starship 信息 | 根据当前目录和项目自动显示 |

透明背景需要桌面合成器支持。Xfce 可在 **窗口管理器微调 → 合成器** 中启用显示合成。背景下方如果有应用窗口，会透出应用内容；它不是只显示桌面壁纸的背景图。

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

确认当前使用 zsh、已进入 tmux（除 Ctrl+T 外），并检查桌面或 VS Code 有没有拦截这些按键。可以先在独立终端（Konsole / XFCE Terminal / GNOME Terminal）测试，再用第四节的前缀快捷键作为替代。

### 透明效果和原电脑不完全一样

透明效果受合成器、壁纸、背后窗口、GTK 主题和字体渲染影响。本包不会修改全局桌面主题和任务栏，因此不保证两台电脑的整个桌面完全相同。GNOME 标准终端不支持透明度时会明确跳过。

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
| `~/.config/konsolerc`、`~/.local/share/konsole/TerminalKit.*` | KDE Konsole 外观及专用 profile |
| XFCE 的 `xfce4-terminal` 配置通道或旧版 terminalrc | XFCE 外观设置 |
| GNOME Terminal 的 dconf 配置 | 字体、尺寸、滚动条及支持的外观项 |
| `~/.local/bin/terminal-kit` | 用目标终端专用参数打开新窗口；完整安装时启动 zsh |
| `~/.local/share/applications/terminal-kit.desktop` | 完整安装的应用菜单入口 |
| `~/.local/libexec/tmux-clipboard` | 按 X11 / Wayland 选择剪贴板工具 |
| `~/.config/Code/User/settings.json` | 仅 `--vscode` 时修改 |

### 恢复安装前的配置

在更新后的仓库目录中操作（**旧备份内的旧 restore.py 不会随着 git pull 自动升级**）：

```bash
git pull --ff-only
bash install.sh --list-backups
```

列表会标明备份是否包含 `.zshrc`。两种恢复目标：

```bash
# 仅撤销最近一次安装；最近一次可能只是外观修复，不包含 shell 皮肤
bash install.sh --restore

# 按时间倒序恢复全部现存备份，回到最早记录的状态
bash install.sh --restore original
```

`original` 会覆盖这些备份涉及文件的后续修改。如果最早备份之前就已美化，或早期备份丢失，无法凭空还原更早的系统默认主题。

也可明确指定某次备份：

```bash
bash install.sh --restore ~/.local/state/manjaro-terminal-kit/实际时间戳
```

**Konsole 正在运行时，安装和新版恢复会等待它关闭后再写入。** 先保存工作，再关闭所有 Konsole 窗口，不要注销桌面。后台最多等待 15 分钟，不会强制关闭任何窗口；完成信息分别记录在：

```text
~/.local/state/manjaro-terminal-kit/apply-after-close.log
~/.local/state/manjaro-terminal-kit/restore-after-close.log
```

完成后不会自动打开 Konsole。请用文件管理器查看日志，确认出现“配置已保存”或“恢复完成”后，再手动打开一个终端。如果超时，没有进行这次写入，需要重新执行。同一用户同时只能运行一个 Konsole 安装或恢复任务；重复执行会提示已有任务，既不会排队，也不会再创建后台任务。

恢复后请先在 **新开的终端、tmux 外** 检查皮肤。已有 zsh 的提示符和 tmux 状态栏保存在进程内，不会随配置文件回退自动改变。脚本不终止工作会话，也不修改通过 `chsh` 设置的登录 shell。

### 恢复皮肤后仍想隐藏红框的窗口栏

恢复原样会带回原有标题栏/工具栏，这是恢复行为，不是隐藏操作。若只想去掉 Konsole 的窗口栏，保留当前原生配色、透明度、字体及提示符：

```bash
bash install.sh --hide-chrome
```

此操作也会备份，且等所有 Konsole 窗口关闭后应用。它只处理标题栏、边框、菜单、工具栏、标签栏及旧布局缓存，不重装皮肤。不要用 `--terminal-only` 替代它：`--terminal-only` 仍会更换终端配色、字体、透明度和尺寸。

## 9. 适用范围与验证情况

- 包内工具版本：Starship **1.26.0**、fzf **0.74.5**、tmux **3.7c**。
- 面向 **x86_64 Manjaro KDE Plasma / Xfce / GNOME**，支持的终端及限制见本文开头。ARM、Windows 不在安装范围内。
- 包内校验、本机只读依赖检查、Python/zsh/Bash 语法和 Starship TOML 解析已检查。
- 已在本机 Xfce 做只读预检；自动化测试覆盖桌面分流、KDE 文件写入及备份恢复、GNOME 键备份和不支持项提示。**尚未在真实 KDE/GNOME 桌面完成视觉验收**，不能承诺所有版本外观完全一致。
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

## 单独应用原生终端外观与高级用法

在另一台电脑的仓库目录中执行。KDE 示例：

```bash
git pull --ff-only
bash install.sh --terminal-only
~/.local/bin/terminal-kit
```

默认自动按桌面选择，无须额外参数。仅需覆盖自动结果时使用 `--terminal konsole`、`--terminal xfce4-terminal` 或 `--terminal gnome-terminal`。`--check` 只检查，不修改和备份；真正应用时才创建备份。

`--terminal-only` 会配置原生终端并安装配套字体，不修改 zsh/tmux。KDE 会创建独立的 `TerminalKit.profile` 与 `TerminalKit.colorscheme`，切换 Konsole 默认 profile，并保存菜单、工具栏、标题栏等默认选项；不修改全局 KWin 主题。

### 为什么 KDE 旧窗口没变化

Konsole 进程会缓存配置，KDE 还可能从 `konsolestaterc` 恢复工具栏布局。新版会备份并清理相关 `State` 布局键，并在所有 Konsole 窗口关闭后应用，避免旧进程写回覆盖。GNOME Headerbar 设置同样可能需要保存任务后重启终端服务。

### 备份与恢复的范围

所有将被修改的文件都会在写入前备份；原来不存在的文件会记录为新建，恢复时删除。支持 `XDG_CONFIG_HOME` / `XDG_DATA_HOME` 自定义目录；KDE 布局状态同时遵循 `XDG_STATE_HOME`。

- **KDE**：`konsolerc`、Terminal Kit profile/colorscheme、字体和 `terminal-kit` 启动脚本。
- **Xfce**：逐项保存 xfconf 原值，或备份旧版 terminalrc；另保存字体及启动脚本。
- **GNOME**：逐项备份 dconf 原始用户值，恢复时写回原值或恢复为系统默认；另保存字体及启动脚本。
- **完整安装**：还会备份 zsh/tmux/Starship 配置及被替换的工具。

安装会打印具体备份目录以及 `python3 /备份目录/restore.py`。指定备份时仅恢复该次项目；`--restore original` 则倒序应用全部现存备份。旧备份请优先用更新后仓库的恢复入口处理。

### 配置依据

- [Konsole 设置项源码](https://github.com/KDE/konsole/blob/master/src/settings/konsole.kcfg)
- [Konsole 配置文件字段](https://github.com/KDE/konsole/blob/master/src/profile/Profile.cpp)
- [GNOME Terminal GSettings schema](https://github.com/GNOME/gnome-terminal/blob/master/src/org.gnome.Terminal.gschema.xml)
- [XFCE 配置后端迁移说明](https://forum.xfce.org/viewtopic.php?id=16911)

### KDE 安装报 `MissingSectionHeaderError`

旧版安装器无法读取以 `MenuBar=Disabled` 等无分组键开头的 `konsolerc`。已改为保留原文、仅更新目标键，不需要删除自己的配置文件。更新后重试：

```bash
git pull --ff-only && bash install.sh
```

若需要恢复到失败安装之前，请使用那次输出的 `python3 /备份目录/restore.py`。再次安装会新建备份，新的备份代表重试前状态，不是第一次失败前的状态。

KDE 工具栏布局处理依据 [KMainWindow 的恢复顺序](https://github.com/KDE/kxmlgui/blob/master/src/kmainwindow.cpp)：序列化的 `State` 会在工具栏可见性设置之后加载，因此也需要处理该缓存。

### Konsole 标题栏隐藏了，但“新建标签页 / 复制 / 粘贴”还在

这些按钮属于工具栏。此前写入的 `Visible=Disabled` 不被当前 KToolBar 用于控制可见性，已移除。新版使用 Konsole 官方 `--hide-toolbars` 启动参数，并备份后更新用户级 `org.kde.konsole.desktop` 的主入口及新窗口/新标签页操作。系统级桌面文件不修改，恢复时用户级入口也会还原。

```bash
git pull --ff-only && bash install.sh --hide-chrome
```

按提示保存任务、关闭全部 Konsole 窗口；用文件管理器确认日志显示完成后，再从应用菜单的 Konsole 或 Terminal Kit 手动打开新窗口。若桌面快捷方式是你单独复制的文件、或自己直接运行 `konsole`，它可能不经过这个入口，可明确运行：

```bash
konsole --separate --hide-menubar --hide-tabbar --hide-toolbars
```

依据：[KToolBar 的配置读取实现](https://github.com/KDE/kxmlgui/blob/master/src/ktoolbar.cpp)、[Konsole 官方启动选项](https://docs.kde.org/stable_kf6/en/konsole/konsole/command-line-options.html)。当前机器没有 Konsole，已检查官方实现及启动入口生成/恢复测试；实际 KDE 窗口仍需目标电脑验证。
