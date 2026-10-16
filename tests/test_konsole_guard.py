import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import konsole_guard


ROOT = Path(__file__).resolve().parents[1]

# Exercise the same descriptor handoff as the real installer without opening a
# terminal, waiting for desktop processes, or touching the user's configuration.
WORKER = '''\
import argparse
from pathlib import Path
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--module-root')
parser.add_argument('--lock-path')
parser.add_argument('--ready')
parser.add_argument('--release')
parser.add_argument('--fail', action='store_true')
parser.add_argument('--wait-konsole', action='store_true')
parser.add_argument('--konsole-lock-fd', type=int)
args = parser.parse_args()
sys.path.insert(0, args.module_root)
from konsole_guard import operation_lock

assert args.wait_konsole
assert args.konsole_lock_fd is not None
with operation_lock(Path(args.lock_path), inherited_fd=args.konsole_lock_fd):
    Path(args.ready).write_text('locked')
    deadline = time.monotonic() + 10
    while not Path(args.release).exists():
        if time.monotonic() > deadline:
            raise RuntimeError('test worker timed out')
        time.sleep(.01)
    if args.fail:
        raise RuntimeError('simulated apply failure')
'''

CONTENDER = '''\
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
from konsole_guard import operation_lock

try:
    with operation_lock(Path(sys.argv[2])):
        Path(sys.argv[3]).write_text('started')
except RuntimeError as error:
    print(error)
    sys.exit(23)
'''


class OperationLockTests(unittest.TestCase):
    def contender(self, lock_path, started):
        return subprocess.run(
            [sys.executable, '-c', CONTENDER, str(ROOT), str(lock_path), str(started)],
            text=True, capture_output=True, timeout=3)

    def assert_rejected(self, lock_path, started):
        result = self.contender(lock_path, started)
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertIn('已有安装或恢复任务', result.stdout)
        self.assertFalse(started.exists(), 'a duplicate operation must not start')

    def assert_available(self, lock_path, started):
        result = self.contender(lock_path, started)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(started.read_text(), 'started')

    def test_normal_exit_releases_lock_for_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            lock_path = root / 'operation.lock'
            with konsole_guard.operation_lock(lock_path) as lock:
                self.assertFalse(lock.closed)
                self.assert_rejected(lock_path, root / 'duplicate-started')
            self.assertTrue(lock.closed)
            self.assert_available(lock_path, root / 'retry-started')

    def test_exception_releases_lock_for_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            lock_path = root / 'operation.lock'
            with self.assertRaisesRegex(ValueError, 'simulated failure'):
                with konsole_guard.operation_lock(lock_path) as lock:
                    raise ValueError('simulated failure')
            self.assertTrue(lock.closed)
            self.assert_available(lock_path, root / 'retry-started')

    def test_failed_background_spawn_releases_lock_for_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            lock_path = root / 'operation.lock'
            with self.assertRaisesRegex(OSError, 'cannot spawn'):
                with konsole_guard.operation_lock(lock_path) as lock:
                    with patch('konsole_guard.subprocess.Popen', side_effect=OSError('cannot spawn')):
                        konsole_guard.defer(root / 'worker.py', [], root / 'worker.log', lock)
            self.assert_available(lock_path, root / 'retry-started')

    def test_background_inherits_lock_without_unlock_gap_and_allows_retry(self):
        for fail in (False, True):
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                worker = root / 'worker.py'
                worker.write_text(WORKER)
                lock_path = root / 'operation.lock'
                ready = root / 'ready'
                release = root / 'release'
                log = root / 'worker.log'
                args = ['--module-root', str(ROOT), '--lock-path', str(lock_path),
                        '--ready', str(ready), '--release', str(release)]
                if fail:
                    args.append('--fail')
                process = None
                try:
                    output = io.StringIO()
                    with konsole_guard.operation_lock(lock_path) as lock:
                        with contextlib.redirect_stdout(output):
                            process = konsole_guard.defer(worker, args, log, lock)
                        self.assertIsInstance(process, subprocess.Popen)
                    # The parent closes its descriptor immediately, before the
                    # worker reports readiness. The child must retain the lock.
                    self.assertTrue(lock.closed)
                    self.assert_rejected(lock_path, root / 'duplicate-early')
                    deadline = time.monotonic() + 3
                    while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                        time.sleep(.01)
                    self.assertTrue(ready.exists(), log.read_text())
                    self.assert_rejected(lock_path, root / 'duplicate-late')
                    self.assertIn('手动', output.getvalue())
                    self.assertNotIn('完成后会自动打开', output.getvalue())
                    release.write_text('finish')
                    returncode = process.wait(timeout=3)
                    self.assertEqual(returncode == 0, not fail, log.read_text())
                    self.assert_available(lock_path, root / 'retry-started')
                finally:
                    if process is not None and process.poll() is None:
                        process.terminate()
                        process.wait(timeout=3)


if __name__ == '__main__':
    unittest.main()
