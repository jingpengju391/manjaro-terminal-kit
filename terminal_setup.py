"""Desktop detection and backed-up, terminal-specific appearance settings."""
import ast
import configparser
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def detect(env=None, which=None, requested='auto'):
    which = shutil.which if which is None else which
    env = os.environ if env is None else env
    name = (env.get('XDG_CURRENT_DESKTOP', '') + ':' + env.get('DESKTOP_SESSION', '')).lower()
    desktop = next((label for words, label in [(('kde', 'plasma'), 'KDE Plasma'),
                    (('xfce',), 'Xfce'), (('gnome',), 'GNOME')]
                    if any(w in name for w in words)), '未知')
    session = env.get('XDG_SESSION_TYPE') or ('wayland' if env.get('WAYLAND_DISPLAY') else 'x11' if env.get('DISPLAY') else '未知')
    if requested != 'auto':
        if not which(requested):
            raise RuntimeError(f'未安装指定终端：{requested}')
        return desktop, session, requested
    expected = {'KDE Plasma': 'konsole', 'Xfce': 'xfce4-terminal', 'GNOME': 'gnome-terminal'}
    if desktop == 'GNOME' and not which('gnome-terminal') and (which('ptyxis') or which('kgx')):
        raise RuntimeError('检测到 GNOME，但只有 Ptyxis/Console。它们不是 GNOME Terminal，不能套用相同设置。请安装 gnome-terminal 后用 --terminal gnome-terminal，或提供实际终端名称。')
    if desktop in expected:
        terminal = expected[desktop]
        if not which(terminal):
            raise RuntimeError(f'检测到 {desktop}，但未找到 {terminal}。请用 --terminal 指定已安装终端。')
    else:
        found = [t for t in expected.values() if which(t)]
        if len(found) != 1:
            raise RuntimeError('不能唯一识别目标终端。请用 --terminal konsole、xfce4-terminal 或 gnome-terminal 明确指定。')
        terminal = found[0]
    return desktop, session, terminal


def config_path(home):
    return Path(os.environ.get('XDG_CONFIG_HOME', str(home / '.config')))


def data_path(home):
    return Path(os.environ.get('XDG_DATA_HOME', str(home / '.local/share')))


def read_ini(path):
    # KConfig permits ungrouped keys before the first header. This synthetic
    # group is read-only and is never serialized into the real file.
    cfg = configparser.ConfigParser(interpolation=None, strict=False, delimiters=('=',))
    cfg.optionxform = str
    if path.exists():
        cfg.read_string('[__ungrouped__]\n' + path.read_text())
    return cfg


def edit_ini(path, changes, keep):
    """Patch only owned keys, preserving KConfig root entries and comments."""
    original = path.read_text() if path.exists() else ''
    pending = {group: dict(values) for group, values in changes.items()}
    output = []
    group = None

    def flush():
        if group in pending:
            for key, value in pending[group].items():
                output.append(f'{key}={value}\n')
            pending[group].clear()

    for line in original.splitlines(keepends=True):
        header = re.fullmatch(r'\s*\[(.*)\]\s*', line)
        if header:
            flush()
            group = header.group(1)
        elif group in changes and '=' in line and not line.lstrip().startswith(('#', ';')):
            key = line.split('=', 1)[0].strip()
            if key in changes[group]:
                output.append(f'{key}={changes[group][key]}\n')
                pending[group].pop(key, None)
                continue
        output.append(line if line.endswith('\n') else line + '\n')
    flush()
    for name, values in pending.items():
        if values:
            output.append(f'\n[{name}]\n')
            output.extend(f'{key}={value}\n' for key, value in values.items())
    keep(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink(): path.unlink()
    path.write_text(''.join(output))


def preflight(terminal):
    """Read only; errors occur before any installation writes."""
    if terminal == 'xfce4-terminal':
        version = run('xfce4-terminal', '--version')
        match = re.search(r'xfce4-terminal\s+(\d+)\.(\d+)', version)
        if not match:
            raise RuntimeError('无法识别 XFCE Terminal 版本。')
        if tuple(map(int, match.groups())) >= (1, 1):
            run('xfconf-query', '-l')
        return {'legacy': tuple(map(int, match.groups())) < (1, 1)}
    if terminal == 'konsole':
        version = run('konsole', '--version')
        match = re.search(r'(\d+)\.(\d+)', version)
        if not match or tuple(map(int, match.groups())) < (21, 12):
            raise RuntimeError('Konsole 版本过旧或无法识别；此配置支持 Konsole 21.12 及以上。')
        return {'help': run('konsole', '--help')}
    # Do not guess another GNOME terminal's schema or profile UUID.
    schemas = run('gsettings', 'list-schemas').splitlines()
    if 'org.gnome.Terminal.ProfilesList' not in schemas:
        raise RuntimeError('缺少 GNOME Terminal 的 GSettings schema，不能应用设置。')
    uuid = ast.literal_eval(run('gsettings', 'get', 'org.gnome.Terminal.ProfilesList', 'default'))
    if not re.fullmatch(r'[0-9a-fA-F-]{36}', uuid):
        raise RuntimeError('GNOME Terminal 没有有效默认配置；请先打开一次再重试。')
    path = f'/org/gnome/terminal/legacy/profiles:/:{uuid}/'
    schema = 'org.gnome.Terminal.Legacy.Profile:' + path
    keys = set(run('gsettings', 'list-keys', schema).splitlines())
    needed = {'font', 'use-system-font', 'default-size-columns', 'default-size-rows', 'scrollbar-policy'}
    if not needed <= keys:
        raise RuntimeError('此 GNOME Terminal 缺少所需设置键，未修改配置。')
    for key in needed:
        if run('gsettings', 'writable', schema, key) != 'true':
            raise RuntimeError(f'GNOME 设置被系统策略锁定：{key}')
    return {'schema': schema, 'path': path, 'keys': keys,
            'global_keys': set(run('gsettings', 'list-keys', 'org.gnome.Terminal.Legacy.Settings').splitlines())}


def configure(terminal, info, home, props, keep, manifest, save):
    notes = []
    if terminal == 'xfce4-terminal':
        if info['legacy']:
            edit_ini(config_path(home) / 'xfce4/terminal/terminalrc', {'Configuration': {
                ''.join(part.capitalize() for part in p['name'].split('-')): p['value'] for p in props}}, keep)
        else:
            for p in props:
                key = '/' + p['name']
                old = subprocess.run(['xfconf-query', '-c', 'xfce4-terminal', '-p', key], capture_output=True, text=True)
                manifest['properties'].append({'name': key, 'type': p['type'], 'existed': old.returncode == 0, 'value': old.stdout.strip()})
                save()
                run('xfconf-query', '-c', 'xfce4-terminal', '-p', key, '--create', '-t', p['type'], '-s', p['value'])
                if run('xfconf-query', '-c', 'xfce4-terminal', '-p', key) != p['value']:
                    # Doubles may be serialized with trailing zeroes.
                    if p['type'] != 'double' or float(run('xfconf-query', '-c', 'xfce4-terminal', '-p', key)) != float(p['value']):
                        raise RuntimeError('XFCE 配置回读不一致：' + key)
        command = ['xfce4-terminal', '--disable-server', '--hide-menubar', '--hide-toolbar', '--hide-borders']
        notes.append('已写入 XFCE：隐藏标题栏/边框、菜单栏、工具栏、滚动条；120×24；透明背景深度 0.75。')
    elif terminal == 'konsole':
        rc = config_path(home) / 'konsolerc'
        edit_ini(rc, {'Desktop Entry': {'DefaultProfile': 'TerminalKit.profile'},
                     'KonsoleWindow': {'RemoveWindowTitleBarAndFrame': 'true', 'RememberWindowSize': 'false'},
                     'MainWindow': {'MenuBar': 'Disabled'},
                     'MainWindow][Toolbar mainToolBar': {'Visible': 'Disabled'},
                     'MainWindow][Toolbar sessionToolbar': {'Visible': 'Disabled'},
                     'TabBar': {'TabBarVisibility': 'AlwaysHideTabBar'}}, keep)
        folder = data_path(home) / 'konsole'
        edit_ini(folder / 'TerminalKit.profile', {
            'General': {'Name': 'Terminal Kit', 'Parent': 'FALLBACK/', 'TerminalColumns': '120', 'TerminalRows': '24'},
            'Appearance': {'Font': 'MesloLGS NF,10,-1,5,50,0,0,0,0,0', 'ColorScheme': 'TerminalKit'},
            'Scrolling': {'ScrollBarPosition': '2', 'HistorySize': '50000'}}, keep)
        edit_ini(folder / 'TerminalKit.colorscheme', {
            'General': {'Description': 'Terminal Kit', 'Opacity': '0.75', 'Blur': 'false'},
            'Background': {'Color': '30,33,39'}, 'Foreground': {'Color': '220,223,228'}}, keep)
        # Verify files, but do not claim a running Konsole window has reloaded them.
        if read_ini(rc).get('KonsoleWindow', 'RemoveWindowTitleBarAndFrame') != 'true':
            raise RuntimeError('Konsole 配置回读失败。')
        command = ['konsole', '--separate', '--profile', 'TerminalKit', '--hide-menubar', '--hide-tabbar']
        if '--hide-toolbars' in info['help']:
            command.append('--hide-toolbars')
        else:
            notes.append('此 Konsole 不提供 --hide-toolbars；已写入工具栏可见性配置，需新窗口验证。')
        notes.append('已写入 Konsole 专用配置：默认 Terminal Kit profile；无标题栏/边框；隐藏菜单/标签/工具栏/滚动条；120×24；背景不透明度 75%。')
        notes.append('KDE 配置文件已保存；已有 Konsole 进程可能保留或在退出时写回旧状态。保存任务、关闭旧窗口后重新应用，或先用 terminal-kit 打开独立窗口验证。')
    else:
        def setting(schema, key, value, path):
            if run('gsettings', 'writable', schema, key) != 'true':
                notes.append(f'跳过被系统锁定的 GNOME 设置：{key}')
                return
            raw = run('dconf', 'read', path + key)
            manifest.setdefault('dconf', []).append({'path': path + key, 'value': raw})
            save()
            run('gsettings', 'set', schema, key, value)
            if not run('gsettings', 'get', schema, key):
                raise RuntimeError('GNOME 配置回读失败：' + key)
        for key, value in {'font': "'MesloLGS NF 10'", 'use-system-font': 'false',
                           'default-size-columns': '120', 'default-size-rows': '24', 'scrollbar-policy': "'never'"}.items():
            setting(info['schema'], key, value, info['path'])
        if 'default-show-menubar' in info['global_keys']:
            setting('org.gnome.Terminal.Legacy.Settings', 'default-show-menubar', 'false', '/org/gnome/terminal/legacy/')
        if 'headerbar' in info['global_keys']:
            setting('org.gnome.Terminal.Legacy.Settings', 'headerbar', 'false', '/org/gnome/terminal/legacy/')
        if {'use-transparent-background', 'background-transparency-percent'} <= info['keys']:
            setting(info['schema'], 'use-transparent-background', 'true', info['path'])
            setting(info['schema'], 'background-transparency-percent', '25', info['path'])
            notes.append('检测到发行版透明度扩展，已设置 25% 透明度。')
        else:
            notes.append('不支持：此 GNOME Terminal 没有背景透明度设置，未修改透明度。')
        notes.append('已写入 GNOME Terminal：字体、120×24、隐藏滚动条；启动器隐藏菜单。Headerbar 关闭需重启 terminal-server（请先保存任务）。')
        notes.append('不支持：GNOME 下没有通用的无标题栏/无边框开关。关闭 Headerbar 不等于移除窗口装饰；未安装扩展或修改全局 GTK 样式。')
        command = ['gnome-terminal', '--hide-menubar', '--geometry=120x24']
    launcher = home / '.local/bin/terminal-kit'
    keep(launcher)
    launcher.parent.mkdir(parents=True, exist_ok=True)
    if launcher.is_symlink():
        launcher.unlink()
    launcher.write_text('#!/bin/sh\nexec ' + shlex.join(command) + ' "$@"\n')
    launcher.chmod(0o755)
    return notes
