#!/usr/bin/python3
import subprocess,sys,fcntl,os
from pathlib import Path
exe=str(Path.home()/'.local/bin/tmux')
def run(*args):return subprocess.check_output([exe,*args],text=True).strip()
w=sys.argv[1]
try:
 lockdir=Path(os.environ.get('XDG_RUNTIME_DIR',str(Path.home()/'.cache')))
 lockdir.mkdir(parents=True,exist_ok=True)
 lock=open(lockdir/'tmux-monitor-create.lock','w')
 fcntl.flock(lock,fcntl.LOCK_EX)
 panes=run('list-panes','-t',w,'-F','#{pane_id} #{@system_monitor} #{pane_dead} #{pane_height}').splitlines()
 for entry in panes:
  fields=entry.split()
  if len(fields)==4 and fields[1]=='1':
   if fields[3]!='3':
    run('resize-pane','-t',fields[0],'-y','3')
   if fields[2]=='1':
    run('respawn-pane','-t',fields[0],str(Path.home()/'.local/libexec/tmux-monitor.py'))
   sys.exit(0)
 old=run('display-message','-p','-t',w,'#{pane_id}')
 pane=run('split-window','-d','-v','-b','-f','-l','3','-t',w,'-P','-F','#{pane_id}',str(Path.home()/'.local/libexec/tmux-monitor.py'))
 run('set-option','-p','-t',pane,'@system_monitor','1')
 run('set-option','-p','-t',pane,'remain-on-exit','on')
 run('select-pane','-t',old)
except subprocess.CalledProcessError:pass
