#!/usr/bin/python3
import os,time,shutil,sys
from pathlib import Path
from collections import deque

def read():
    v=list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:9]))
    mem={k:int(v.split()[0]) for k,v in (x.split(':',1) for x in Path('/proc/meminfo').read_text().splitlines())}
    names={f[0] for x in Path('/proc/net/route').read_text().splitlines()[1:] if (f:=x.split())[1]=='00000000' and int(f[3],16)&1}
    rx=tx=0
    for x in Path('/proc/net/dev').read_text().splitlines()[2:]:
        name,data=x.split(':',1)
        if name.strip() in names:
            f=data.split();rx+=int(f[0]);tx+=int(f[8])
    return time.monotonic(),sum(v),v[3]+v[4],mem,rx,tx,names

def spark(data,width,ceiling=None):
    vals=list(data)[-width:];maxval=ceiling or max(max(vals,default=0),1)
    chars='▁▂▃▄▅▆▇█'
    return '▁'*max(0,width-len(vals))+''.join(chars[min(7,max(0,int(v/maxval*7)))] for v in vals)
def speed(v):return f'{v/1048576:.1f}M/s' if v>=1048576 else f'{v/1024:.1f}K/s'
def color(s,c):return f'\033[38;2;{c}m{s}\033[0m'
series=[deque(maxlen=600) for _ in range(4)]
old=read()
print('\033[?25l\033[2J',end='',flush=True)
try:
 while True:
    time.sleep(1)
    cur=read();dt=max(.001,cur[0]-old[0]);delta=max(1,cur[1]-old[1])
    cpu=max(0,min(100,100*(1-(cur[2]-old[2])/delta)))
    mem=cur[3];used=mem['MemTotal']-mem['MemAvailable'];pct=used/mem['MemTotal']*100
    down=max(0,cur[4]-old[4])/dt if cur[6]==old[6] else 0
    up=max(0,cur[5]-old[5])/dt if cur[6]==old[6] else 0
    for q,v in zip(series,[cpu,pct,down,up]):q.append(v)
    width=shutil.get_terminal_size().columns
    labels=[f'CPU {cpu:3.0f}%',f'RAM {used/1048576:.1f}/{mem["MemTotal"]/1048576:.1f}G',f'↓ {speed(down)}',f'↑ {speed(up)}']
    stamp=time.strftime('%m-%d %H:%M:%S');colors=['229;192;123','152;195;121','97;175;239','198;120;221']
    available=width-len(stamp)-sum(map(len,labels))-19
    graph=max(0,available//4)
    parts=[];visible=0
    for label,q,c,limit in zip(labels,series,colors,[100,100,None,None]):
      t=label+(' '+spark(q,graph,limit) if graph else '')
      parts.append(color(t,c));visible+=len(t)
    line='  '.join(parts)+'  '+color(stamp,'171;178;191');visible+=8+len(stamp)
    if visible>width-2:
      line='  '.join(color(t,c) for t,c in zip(labels[:2],colors));visible=sum(map(len,labels[:2]))+2
    pad=max(0,(width-visible)//2)
    sys.stdout.write('\033[H\033[2K\n\033[2K'+' '*pad+line+'\n\033[2K');sys.stdout.flush()
    old=cur
except (KeyboardInterrupt,BrokenPipeError):pass
finally:print('\033[?25h',end='',flush=True)
