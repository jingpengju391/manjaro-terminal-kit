#!/usr/bin/env python3
import json,shutil,subprocess
from pathlib import Path
b=Path(__file__).resolve().parent;h=Path.home();m=json.loads((b/'manifest.json').read_text())
for x in reversed(m['files']):
 dst=h/x['path']
 if dst.exists() or dst.is_symlink():dst.unlink()
 if x['existed']:
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(b/'files'/x['path'],dst,follow_symlinks=False)
for x in m['properties']:
 cmd=['xfconf-query','-c','xfce4-terminal','-p',x['name']]
 cmd+=['--create','-t',x['type'],'-s',x['value']] if x['existed'] else ['--reset']
 subprocess.run(cmd,check=True)
subprocess.run(['fc-cache','-f'],check=True)
print('原配置已恢复。请重新打开终端；默认登录 shell 如已手动更改，请自行用 chsh 恢复。')
