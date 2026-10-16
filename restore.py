#!/usr/bin/env python3
"""Restore only the files/properties recorded by this installation."""
import json
from pathlib import Path
import shutil
import subprocess

b = Path(__file__).resolve().parent
h = Path.home()
m = json.loads((b / 'manifest.json').read_text())
for x in reversed(m['files']):
    dst = Path(x['absolute']) if 'absolute' in x else h / x['path']
    if dst.exists() or dst.is_symlink(): dst.unlink()
    if x['existed']:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(b / 'files' / x.get('stored', x.get('path', '')), dst, follow_symlinks=False)
for x in reversed(m.get('properties', [])):
    cmd = ['xfconf-query', '-c', 'xfce4-terminal', '-p', x['name']]
    cmd += ['--create', '-t', x['type'], '-s', x['value']] if x['existed'] else ['--reset']
    subprocess.run(cmd, check=True)
for x in reversed(m.get('dconf', [])):
    cmd = ['dconf', 'write', x['path'], x['value']] if x['value'] else ['dconf', 'reset', x['path']]
    subprocess.run(cmd, check=True)
subprocess.run(['fc-cache', '-f'], check=True)
print('本次记录的原文件和设置已恢复。保存任务后重新打开终端；运行中的应用可能保留旧设置。默认 shell 如曾用 chsh 修改，需手动恢复。')
