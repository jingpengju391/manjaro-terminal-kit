#!/usr/bin/env python3
"""Install the personal terminal preset. Never run as root."""
import argparse, datetime, json, os, platform, shutil, subprocess, re, configparser
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument('--check',action='store_true',help='Read-only prerequisite check')
ap.add_argument('--vscode',action='store_true',help='Also merge VS Code terminal font; requires plain JSON settings')
ap.add_argument('--terminal-only',action='store_true',help='Only apply XFCE terminal appearance; back up settings first')
a=ap.parse_args()
if os.geteuid()==0: raise SystemExit('请用普通桌面用户运行，不要 sudo bash install.sh。')
if platform.machine()!='x86_64': raise SystemExit('此离线工具包仅支持 x86_64。')
h=Path.home(); base=Path(__file__).resolve().parent; p=base/'payload'
required=['zsh','python3','xfconf-query','xfce4-terminal','fc-cache']
if a.terminal_only: required=['python3','xfconf-query','xfce4-terminal','fc-cache']
missing=[x for x in required if not shutil.which(x)]
for f in ['/usr/share/zsh/manjaro-zsh-config','/usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh','/usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh']:
 if not a.terminal_only and not Path(f).is_file(): missing.append(f)
if missing:
 print('缺少依赖：',*missing,sep='\n')
 raise SystemExit('请先执行：sudo pacman -Syu --needed zsh manjaro-zsh-config zsh-autosuggestions zsh-syntax-highlighting xfce4-terminal python fontconfig python-gobject gtk3')
version_text=subprocess.check_output(['xfce4-terminal','--version'],text=True)
match=re.search(r'xfce4-terminal\s+(\d+)\.(\d+)',version_text)
if not match: raise SystemExit('无法识别 XFCE Terminal 版本，请提供 xfce4-terminal --version 的输出。')
legacy=tuple(map(int,match.groups())) < (1,1)
if not legacy:
 subprocess.run(['xfconf-query','-l'],check=True,stdout=subprocess.DEVNULL)
print('终端设置后端：'+('terminalrc（旧版）' if legacy else 'xfconf'))
vs=h/'.config/Code/User/settings.json'; vsdata=None
if a.vscode:
 try: vsdata=json.loads(vs.read_text()) if vs.exists() else {}
 except ValueError: raise SystemExit('VS Code 配置含注释或尾逗号；请不带 --vscode 安装，再手动设置字体为 MesloLGS NF。')
if a.check:
 print('环境检查通过；未修改任何配置。去掉 --check 才会应用设置。');raise SystemExit()
backup=h/'.local/state/manjaro-terminal-kit'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');backup.mkdir(parents=True)
manifest={'files':[],'properties':[]}
def save(): (backup/'manifest.json').write_text(json.dumps(manifest,indent=2))
def keep(dst):
 rel=str(dst.relative_to(h)); item={'path':rel,'existed':dst.exists() or dst.is_symlink()}
 if item['existed']:
  target=backup/'files'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,target,follow_symlinks=False)
 manifest['files'].append(item);save()
def copy(src,dst):
 keep(dst);dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.is_symlink():dst.unlink()
 shutil.copy2(src,dst)
shutil.copy2(base/'restore.py',backup/'restore.py');save()
if not a.terminal_only:
 for src,dst in [(p/'zshrc',h/'.zshrc'),(p/'tmux.conf',h/'.tmux.conf'),(p/'starship.toml',h/'.config/starship.toml')]:copy(src,dst)
 for folder,target in [('bin','.local/bin'),('libexec','.local/libexec'),('fonts','.local/share/fonts/terminal-kit')]:
  for src in (p/folder).iterdir():copy(src,h/target/src.name)
if legacy:
 terminalrc=h/'.config/xfce4/terminal/terminalrc'
 keep(terminalrc)
 cfg=configparser.ConfigParser(interpolation=None,strict=False)
 cfg.optionxform=str
 if terminalrc.exists(): cfg.read(terminalrc)
 if not cfg.has_section('Configuration'): cfg.add_section('Configuration')
 for prop in json.loads((p/'terminal.json').read_text()):
  key=''.join(part.capitalize() for part in prop['name'].split('-'))
  cfg.set('Configuration',key,prop['value'])
 terminalrc.parent.mkdir(parents=True,exist_ok=True)
 with terminalrc.open('w') as f: cfg.write(f,space_around_delimiters=False)
else:
 for prop in json.loads((p/'terminal.json').read_text()):

  name='/'+prop['name'];typ=prop['type']
  old=subprocess.run(['xfconf-query','-c','xfce4-terminal','-p',name],capture_output=True,text=True)
  manifest['properties'].append({'name':name,'type':typ,'existed':old.returncode==0,'value':old.stdout.strip()});save()
  subprocess.run(['xfconf-query','-c','xfce4-terminal','-p',name,'--create','-t',typ,'-s',prop['value']],check=True)
if vsdata is not None:
 keep(vs);vs.parent.mkdir(parents=True,exist_ok=True)
 vsdata['terminal.integrated.fontFamily']='MesloLGS NF'
 vsdata['terminal.integrated.defaultProfile.linux']='zsh'
 profiles=vsdata.setdefault('terminal.integrated.profiles.linux',{});profiles['zsh']={'path':'/usr/bin/zsh'}
 vs.write_text(json.dumps(vsdata,ensure_ascii=False,indent=4)+'\n')
subprocess.run(['fc-cache','-f'],check=True)
print('\n安装完成。备份与回滚命令：\npython3 '+str(backup/'restore.py'))
print('已应用：隐藏标题栏/边框、菜单栏、工具栏、滚动条；默认 120x24；透明背景。')
print('请新开 XFCE Terminal 窗口查看效果。旧窗口不一定自动改变；不要直接关闭有任务的窗口。')
print('测试新窗口：xfce4-terminal --disable-server --hide-menubar --hide-toolbar --hide-borders')
if a.terminal_only: raise SystemExit()
print('运行 chsh -s /usr/bin/zsh 后重新登录；也可在当前终端执行 exec zsh。')
print('全新终端生效；Ctrl+T 进入 work。已有 tmux 会话请先保存工作后重新创建，避免运行中的旧版本混用。')
