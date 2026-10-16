import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import konsole_guard
import restore


class RestoreTests(unittest.TestCase):
    def make_backup(self, root, name, entries):
        folder = root/name
        (folder/'files').mkdir(parents=True)
        files = []
        for index, (target, content) in enumerate(entries):
            (folder/'files'/str(index)).write_text(content)
            files.append({'absolute': str(target), 'stored': str(index), 'existed': True})
        (folder/'manifest.json').write_text(json.dumps({'files': files, 'terminal': 'konsole'}))
        return folder

    def test_original_replays_full_and_terminal_only_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            root = home/'.local/state/manjaro-terminal-kit'
            shell = home/'.zshrc'; shell.write_text('kit shell')
            rc = home/'konsolerc'; rc.write_text('new kit theme')
            self.make_backup(root, '20260101', [(shell, 'original shell'), (rc, 'original theme')])
            self.make_backup(root, '20260102', [(rc, 'kit theme')])
            with patch('pathlib.Path.home', return_value=home), patch('konsole_guard.running', return_value=False), \
                    patch('subprocess.run'), contextlib.redirect_stdout(io.StringIO()):
                with patch.object(sys, 'argv', ['restore.py', '--backup', 'latest']): restore.main()
                self.assertEqual(shell.read_text(), 'kit shell')
                self.assertEqual(rc.read_text(), 'kit theme')
                with patch.object(sys, 'argv', ['restore.py', '--backup', 'original']): restore.main()
                self.assertEqual(shell.read_text(), 'original shell')
                self.assertEqual(rc.read_text(), 'original theme')

    def test_running_konsole_defers_before_writing_anything(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            rc = home/'konsolerc'; rc.write_text('current')
            folder = self.make_backup(home/'backups', 'first', [(rc, 'original')])
            with patch('pathlib.Path.home', return_value=home), patch('konsole_guard.running', return_value=True), \
                    patch('konsole_guard.defer') as defer, patch('subprocess.run') as run, \
                    patch.object(sys, 'argv', ['restore.py', '--backup', str(folder)]):
                restore.main()
                defer.assert_called_once()
                run.assert_not_called()
                self.assertEqual(rc.read_text(), 'current')

    def test_incomplete_backup_does_not_partially_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            target = home/'file'; target.write_text('current')
            folder = self.make_backup(home/'backups', 'first', [(target, 'original')])
            (folder/'files/0').unlink()
            with patch('pathlib.Path.home', return_value=home), patch.object(sys, 'argv', ['restore.py', '--backup', str(folder)]):
                with self.assertRaisesRegex(RuntimeError, '备份文件缺失'): restore.main()
            self.assertEqual(target.read_text(), 'current')

    def test_deferred_restore_applies_without_opening_a_window(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            target = home/'konsolerc'; target.write_text('current')
            folder = self.make_backup(home/'backups', 'first', [(target, 'original')])
            with patch('pathlib.Path.home', return_value=home), \
                    patch('konsole_guard.wait_until_closed') as wait, \
                    patch('subprocess.run'), patch('subprocess.Popen') as launch, \
                    patch.object(sys, 'argv', ['restore.py', '--backup', str(folder), '--wait-konsole']), \
                    contextlib.redirect_stdout(io.StringIO()):
                restore.main()
            wait.assert_called_once()
            launch.assert_not_called()
            self.assertEqual(target.read_text(), 'original')

    def test_wait_timeout_makes_no_changes(self):
        with patch('konsole_guard.running', return_value=True), patch('time.monotonic', side_effect=[0, 20]):
            with self.assertRaisesRegex(RuntimeError, '超时'): konsole_guard.wait_until_closed(timeout=10)


if __name__ == '__main__': unittest.main()
