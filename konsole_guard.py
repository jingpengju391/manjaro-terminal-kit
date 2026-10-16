"""Wait for the user's Konsole processes to exit without terminating their work."""
from contextlib import contextmanager
import fcntl
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


@contextmanager
def operation_lock(path, inherited_fd=None):
    """Keep one operation active, including across the deferred process handoff."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if inherited_fd is None:
        lock = path.open('a+')
    else:
        lock = os.fdopen(inherited_fd, 'a+')
        os.set_inheritable(lock.fileno(), False)
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('已有安装或恢复任务正在等待或应用配置，请等待它完成；本次未创建新任务。') from None
        yield lock
    finally:
        # Close this reference only: a deferred child may still hold the same lock.
        lock.close()


def defer(script, args, log, lock):
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('a') as stream:
        process = subprocess.Popen([sys.executable, '-u', str(script), *args, '--wait-konsole',
                                    '--konsole-lock-fd', str(lock.fileno())],
                                   stdin=subprocess.DEVNULL, stdout=stream, stderr=stream,
                                   start_new_session=True, pass_fds=(lock.fileno(),))
    print('检测到 Konsole 正在运行，已安排关闭后应用。请先保存任务，再关闭所有 Konsole 窗口（不要注销桌面）。')
    print(f'后台进程：{process.pid}；最多等待 15 分钟。完成记录见：{log}')
    print('请用文件管理器查看完成记录，确认完成后再手动打开 Konsole；不会自动打开或关闭终端。')
    return process
