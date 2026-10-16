"""Wait for the user's Konsole processes to exit without terminating their work."""
import os
from pathlib import Path
import subprocess
import sys
import time


def running():
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit(): continue
        try:
            if directory.stat().st_uid != os.getuid(): continue
            if (directory/'comm').read_text().strip() != 'konsole': continue
            state = (directory/'status').read_text()
            if '\nState:\tZ' not in state: return True
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
    return False


def wait_until_closed(timeout=900):
    deadline = time.monotonic() + timeout
    while running():
        if time.monotonic() >= deadline:
            raise RuntimeError('等待 Konsole 关闭超时，未执行本次配置写入。请重新运行命令。')
        time.sleep(.5)
    # Give the closing process time to finish flushing its state file.
    time.sleep(.5)


def defer(script, args, log):
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('a') as stream:
        process = subprocess.Popen([sys.executable, '-u', str(script), *args, '--wait-konsole'],
                                   stdin=subprocess.DEVNULL, stdout=stream, stderr=stream,
                                   start_new_session=True)
    print('检测到 Konsole 正在运行，已安排关闭后应用。请先保存任务，再关闭所有 Konsole 窗口（不要注销桌面）。')
    print(f'后台进程：{process.pid}；最多等待 15 分钟。完成记录见：{log}')
    print('完成后会自动打开一个新 Konsole；不会自动关闭你的终端或 tmux 会话。')
