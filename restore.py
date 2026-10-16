#!/usr/bin/env python3
"""Restore a snapshot, or replay all snapshots backwards to the earliest recorded state."""
import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import shutil
import subprocess
import sys
import konsole_guard


def snapshots(root):
    return sorted(p.parent for p in root.glob('*/manifest.json'))


def destination(entry, home):
    return Path(entry['absolute']) if 'absolute' in entry else home / entry['path']


def validate(path, manifest):
    for entry in manifest['files']:
        source = path/'files'/entry.get('stored', entry.get('path', ''))
        if entry['existed'] and not (source.exists() or source.is_symlink()):
            raise RuntimeError(f'备份文件缺失：{source}；未开始恢复。')


def restore_backup(path, manifest, home):
    for entry in reversed(manifest['files']):
        target = destination(entry, home)
        if target.exists() or target.is_symlink(): target.unlink()
        if entry['existed']:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path/'files'/entry.get('stored', entry.get('path', '')), target, follow_symlinks=False)
    for entry in reversed(manifest.get('properties', [])):
        command = ['xfconf-query', '-c', 'xfce4-terminal', '-p', entry['name']]
        command += ['--create', '-t', entry['type'], '-s', entry['value']] if entry['existed'] else ['--reset']
        subprocess.run(command, check=True)
    for entry in reversed(manifest.get('dconf', [])):
        command = ['dconf', 'write', entry['path'], entry['value']] if entry['value'] else ['dconf', 'reset', entry['path']]
        subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backup', help='latest / original / 备份目录')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--wait-konsole', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--konsole-lock-fd', type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    home = Path.home()
    root = home/'.local/state/manjaro-terminal-kit'
    available = snapshots(root)
    if args.list:
        for path in available:
            data = json.loads((path/'manifest.json').read_text())
            shell = any(destination(e, home).name == '.zshrc' for e in data['files'])
            print(path.name, data.get('terminal', '旧版'), '含 shell 配置' if shell else '不含 shell 配置')
        if not available: print('没有可恢复备份。')
        return
    selected = args.backup
    if selected is None:
        current = Path(__file__).resolve().parent
        selected = str(current) if (current/'manifest.json').exists() else 'latest'
    if selected in ('original', 'latest'):
        if not available: raise SystemExit('没有可恢复备份。')
        paths = list(reversed(available)) if selected == 'original' else [available[-1]]
    else:
        paths = [Path(selected).expanduser().resolve()]
    records = [(path, json.loads((path/'manifest.json').read_text())) for path in paths]
    for path, manifest in records: validate(path, manifest)
    has_konsole = any(m.get('terminal') == 'konsole' or any(destination(e, home).name == 'konsolerc' for e in m['files']) for _, m in records)
    try:
        with (konsole_guard.operation_lock(root/'konsole-operation.lock', args.konsole_lock_fd)
              if has_konsole else nullcontext()) as lock:
            if has_konsole:
                if args.wait_konsole:
                    konsole_guard.wait_until_closed()
                elif konsole_guard.running():
                    # Pass the resolved snapshot, not the implicit script-location default.
                    konsole_guard.defer(Path(__file__).resolve(), ['--backup', selected], root/'restore-after-close.log', lock)
                    return
            for path, manifest in records:
                restore_backup(path, manifest, home)
                print('已恢复：', path.name)
            subprocess.run(['fc-cache', '-f'], check=True)
            shell = any(destination(e, home).name == '.zshrc' for _, m in records for e in m['files'])
            print('恢复完成。' + ('已还原记录中的 shell/提示符配置。' if shell else '这次备份不含 .zshrc，未恢复 shell/提示符皮肤；可选择 original 回溯全部备份。'))
            print('请新开终端并先在 tmux 外检查；已有 zsh/tmux 会话仍可能保留运行中的旧提示符和状态栏。')
            print('恢复的是备份前的样子，并不额外隐藏标题栏/工具栏。账户登录 shell（chsh）及备份前已存在的主题不会被重置。')
    except RuntimeError as e:
        raise SystemExit(str(e)) from None


if __name__ == '__main__':
    main()
