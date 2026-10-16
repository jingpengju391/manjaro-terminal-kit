import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import terminal_setup as setup

ROOT = Path(__file__).resolve().parents[1]

class DetectionTests(unittest.TestCase):
    def which(self, *names):
        return lambda name: '/usr/bin/' + name if name in names else None

    def test_kde_does_not_pick_installed_xfce(self):
        self.assertEqual(setup.detect({'XDG_CURRENT_DESKTOP': 'KDE', 'XDG_SESSION_TYPE': 'wayland'}, self.which('konsole', 'xfce4-terminal')), ('KDE Plasma', 'wayland', 'konsole'))

    def test_xfce_detected(self):
        self.assertEqual(setup.detect({'XDG_CURRENT_DESKTOP': 'XFCE', 'DISPLAY': ':0'}, self.which('xfce4-terminal'))[2], 'xfce4-terminal')

    def test_gnome_profile_backend(self):
        self.assertEqual(setup.detect({'XDG_CURRENT_DESKTOP': 'GNOME'}, self.which('gnome-terminal'))[2], 'gnome-terminal')

    def test_console_is_not_gnome_terminal(self):
        with self.assertRaisesRegex(RuntimeError, 'Ptyxis/Console'):
            setup.detect({'XDG_CURRENT_DESKTOP': 'GNOME'}, self.which('ptyxis'))

    def test_unknown_multiple_terminals_requires_override(self):
        with self.assertRaises(RuntimeError):
            setup.detect({}, self.which('konsole', 'xfce4-terminal'))

    def test_override_respected(self):
        self.assertEqual(setup.detect({'XDG_CURRENT_DESKTOP': 'KDE'}, self.which('xfce4-terminal'), 'xfce4-terminal')[2], 'xfce4-terminal')

class InstallerTests(unittest.TestCase):
    def test_kde_install_backup_restore_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            config = home / '.config'
            config.mkdir()
            rc = config / 'konsolerc'
            original = '[Desktop Entry]\nDefaultProfile=Personal.profile\n[Unrelated]\nKeep=hello\n'
            rc.write_text(original)
            shell = home / '.zshrc'
            shell.write_text('keep my shell\n')
            env = {'XDG_CONFIG_HOME': str(config), 'XDG_DATA_HOME': str(home / '.local/share'), 'XDG_CURRENT_DESKTOP': 'KDE', 'XDG_SESSION_TYPE': 'wayland'}
            with patch.dict(os.environ, env), patch('pathlib.Path.home', return_value=home), \
                 patch('os.geteuid', return_value=1000), patch('shutil.which', side_effect=lambda n: '/usr/bin/' + n), \
                 patch('terminal_setup.preflight', return_value={'help': '--hide-toolbars'}), \
                 patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0)), \
                 patch('sys.argv', ['install.py', '--terminal-only', '--terminal', 'konsole']), contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(ROOT / 'install.py'), run_name='__main__')
                self.assertEqual(setup.read_ini(rc).get('Unrelated', 'Keep'), 'hello')
                self.assertEqual(setup.read_ini(rc).get('KonsoleWindow', 'RemoveWindowTitleBarAndFrame'), 'true')
                self.assertEqual(shell.read_text(), 'keep my shell\n')
                profile = home / '.local/share/konsole/TerminalKit.profile'
                self.assertEqual(setup.read_ini(profile).get('Scrolling', 'ScrollBarPosition'), '2')
                backups = list((home / '.local/state/manjaro-terminal-kit').iterdir())
                self.assertEqual(len(backups), 1)
                manifest = json.loads((backups[0] / 'manifest.json').read_text())
                self.assertFalse(manifest['properties'])
                self.assertEqual(manifest['terminal'], 'konsole')
                runpy.run_path(str(backups[0] / 'restore.py'), run_name='__main__')
                self.assertEqual(rc.read_text(), original)
                self.assertFalse(profile.exists())
                self.assertFalse((home / '.local/bin/terminal-kit').exists())
                self.assertEqual(shell.read_text(), 'keep my shell\n')

    def test_gnome_records_dconf_before_writing_and_reports_limitations(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            calls=[]; m={'files': [], 'properties': []}
            def fake_run(*args):
                calls.append(args)
                if args[:2] == ('dconf', 'read'): return ''
                if args[:2] == ('gsettings', 'writable'): return 'true'
                if args[:2] == ('gsettings', 'get'): return '120'
                return ''
            info={'schema': 'test:profile', 'path': '/test/profile/', 'keys': set(), 'global_keys': set()}
            with patch('terminal_setup.run', side_effect=fake_run):
                notes=setup.configure('gnome-terminal', info, home, [], lambda p: None, m, lambda: None)
            self.assertEqual(len(m['dconf']), 5)
            self.assertTrue(all(not x['value'] for x in m['dconf']))
            self.assertTrue(any('没有背景透明度' in n for n in notes))
            self.assertTrue(any('无标题栏' in n for n in notes))
            for i, call in enumerate(calls):
                if call[:2] == ('gsettings', 'set'):
                    self.assertEqual(calls[i-1][:2], ('dconf', 'read'))

if __name__ == '__main__': unittest.main()
