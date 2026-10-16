#!/usr/bin/env python3
"""Install user-level shell tools and desktop-specific terminal settings."""
import argparse
import datetime
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import terminal_setup

ap = argparse.ArgumentParser()
ap.add_argument('--check', action='store_true', help='Read-only environment and target check')
ap.add_argument('--vscode', action='store_true', help='Merge VS Code terminal font/profile')
ap.add_argument('--terminal-only', action='store_true', help='Apply terminal appearance and font only')
ap.add_argument('--terminal', choices=['auto', 'konsole', 'xfce4-terminal', 'gnome-terminal'], default='auto')
a = ap.parse_args()
if os.geteuid() == 0:
    raise SystemExit('请用普通桌面用户运行，不要 sudo bash install.sh。')
if platform.machine() != 'x86_64':
    raise SystemExit('此工具包仅支持 x86_64。')
if a.terminal_only and a.vscode:
    ap.error('--terminal-only 与 --vscode 请分别执行。')
h = Path.home()
base = Path(__file__).resolve().parent
p = base / 'payload'
try:
    desktop, session, terminal = terminal_setup.detect(requested=a.terminal)
except RuntimeError as e:
    raise SystemExit(str(e))
print(f'桌面：{desktop}；显示会话：{session}；目标终端：{terminal}')
print('目标按桌面默认终端选择；若你使用其他终端，请用 --terminal 明确指定。')
required = ['python3', terminal, 'fc-cache']
if terminal == 'xfce4-terminal':
    required.append('xfconf-query')
elif terminal == 'gnome-terminal':
    required += ['gsettings', 'dconf']
if not a.terminal_only:
    required.append('zsh')
    if session == 'wayland':
        required.append('wl-copy')
missing = [x for x in required if not shutil.which(x)]
if not a.terminal_only:
    for f in ['/usr/share/zsh/manjaro-zsh-config', '/usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh', '/usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh']:
        if not Path(f).is_file():
            missing.append(f)
if missing:
    print('缺少依赖：', *missing, sep='\n')
    packages = ['python', 'fontconfig', terminal]
    if terminal == 'xfce4-terminal': packages.append('xfconf')
    if terminal == 'gnome-terminal': packages += ['glib2', 'dconf']
    if not a.terminal_only:
        packages += ['zsh', 'manjaro-zsh-config', 'zsh-autosuggestions', 'zsh-syntax-highlighting']
        packages += ['wl-clipboard'] if session == 'wayland' else ['libxmu']
    raise SystemExit('先执行：sudo pacman -Syu --needed ' + ' '.join(packages))
try:
    info = terminal_setup.preflight(terminal)
except (RuntimeError, subprocess.CalledProcessError) as e:
    raise SystemExit(f'终端环境检查失败，未修改配置：{e}')
if terminal == 'gnome-terminal':
    print('GNOME 限制：不保证去除标题栏/边框；透明度仅在发行版提供相应设置键时配置。')
if not a.terminal_only and session not in ['x11', 'wayland']:
    raise SystemExit('无法识别 X11/Wayland；请在目标电脑已登录的桌面会话中安装。')
vs = terminal_setup.config_path(h) / 'Code/User/settings.json'
vsdata = None
if a.vscode:
    try:
        vsdata = json.loads(vs.read_text()) if vs.exists() else {}
    except ValueError:
        raise SystemExit('VS Code 配置含注释或尾逗号；请先不带 --vscode 安装，再手动设置终端字体。')
if a.check:
    print('检查通过；仅验证环境，不写入或备份配置。去掉 --check 才会应用。')
    raise SystemExit()
backup = h / '.local/state/manjaro-terminal-kit' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
backup.mkdir(parents=True)
manifest = {'files': [], 'properties': [], 'dconf': [], 'desktop': desktop, 'terminal': terminal}

def save():
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2))

def keep(dst):
    dst = dst.absolute()
    if any(x.get('absolute') == str(dst) for x in manifest['files']):
        return
    existed = dst.exists() or dst.is_symlink()
    stored = str(len(manifest['files']))
    if existed:
        target = backup / 'files' / stored
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dst, target, follow_symlinks=False)
    manifest['files'].append({'absolute': str(dst), 'stored': stored, 'existed': existed})
    save()

def copy(src, dst):
    keep(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink(): dst.unlink()
    shutil.copy2(src, dst)

shutil.copy2(base / 'restore.py', backup / 'restore.py')
save()
print('备份目录：' + str(backup))
try:
    # Fonts are needed for terminal-only too.
    for src in (p / 'fonts').iterdir():
        copy(src, terminal_setup.data_path(h) / 'fonts/terminal-kit' / src.name)
    if not a.terminal_only:
        for src, dst in [(p / 'zshrc', h / '.zshrc'), (p / 'tmux.conf', h / '.tmux.conf'), (p / 'starship.toml', terminal_setup.config_path(h) / 'starship.toml')]:
            copy(src, dst)
        for folder, target in [('bin', '.local/bin'), ('libexec', '.local/libexec')]:
            for src in (p / folder).iterdir(): copy(src, h / target / src.name)
    notes = terminal_setup.configure(terminal, info, h, json.loads((p / 'terminal.json').read_text()), keep, manifest, save)
    if vsdata is not None:
        keep(vs)
        vs.parent.mkdir(parents=True, exist_ok=True)
        vsdata['terminal.integrated.fontFamily'] = 'MesloLGS NF'
        vsdata['terminal.integrated.defaultProfile.linux'] = 'zsh'
        vsdata.setdefault('terminal.integrated.profiles.linux', {})['zsh'] = {'path': '/usr/bin/zsh'}
        vs.write_text(json.dumps(vsdata, ensure_ascii=False, indent=4) + '\n')
    subprocess.run(['fc-cache', '-f'], check=True)
except Exception:
    print('安装未完成。此前已修改项目的备份仍保留，恢复命令：\npython3 ' + str(backup / 'restore.py'))
    raise
print('\n'.join(notes))
print('配置已保存；不是对现有窗口外观的验证。用 ~/.local/bin/terminal-kit 打开新窗口查看。')
print('恢复命令：\npython3 ' + str(backup / 'restore.py'))
if not a.terminal_only:
    print('用 chsh -s /usr/bin/zsh 设置默认 shell 后重新登录；当前空闲 shell 可执行 exec zsh。')
    print('已有 tmux 会话不会被关闭；新配置需在新会话或手动重新加载后使用。')
