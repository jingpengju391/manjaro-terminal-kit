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
    def test_desktop_entry_patches_all_actions_without_duplicates(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            target = home/'data/applications/org.kde.konsole.desktop'
            target.parent.mkdir(parents=True)
            original = '[Desktop Entry]\nType=Application\nName=Konsole\nExec="/usr/bin/konsole" %U\nActions=NewTab;\n\n[Desktop Action NewTab]\nName=New Tab\nExec=konsole --new-tab\n'
            target.write_text(original)
            before = []
            with patch.dict(os.environ, {'XDG_DATA_HOME': str(home/'data')}):
                setup.konsole_desktop_entry(home, lambda p: before.append(p.read_text()))
                first = target.read_text()
                setup.konsole_desktop_entry(home, lambda p: None)
            self.assertEqual(target.read_text(), first)
            self.assertEqual(first.count('--hide-toolbars'), 2)
            self.assertIn('--hide-toolbars %U', first)
            self.assertIn('--new-tab', first)
            self.assertEqual(before, [original])
            import shutil
            if shutil.which('desktop-file-validate'):
                subprocess.run(['desktop-file-validate', str(target)], check=True)

    def test_chrome_only_preserves_profile_font_and_opacity(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            config = home/'config'; config.mkdir()
            state = home/'state'; state.mkdir()
            rc = config/'konsolerc'
            rc.write_text('[Desktop Entry]\nDefaultProfile=Personal.profile\n[KonsoleWindow]\nRememberWindowSize=true\n[MainWindow]\nState=cached-visible-toolbars\n')
            profile = home/'Personal.profile'; profile.write_text('Font=Personal\nOpacity=.4\n')
            layout = state/'konsolestaterc'; layout.write_text('[MainWindow]\nState=serialized\nWidth=900\n')
            saved = {}
            with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(config), 'XDG_STATE_HOME': str(state), 'XDG_DATA_HOME': str(home/'data'), 'XDG_DATA_DIRS': str(home/'system-data')}):
                setup.configure_konsole_chrome(home, lambda path: saved.setdefault(str(path), path.read_text() if path.exists() else None))
            self.assertEqual(setup.read_ini(rc).get('Desktop Entry', 'DefaultProfile'), 'Personal.profile')
            self.assertEqual(setup.read_ini(rc).get('KonsoleWindow', 'RememberWindowSize'), 'true')
            self.assertNotIn('State=', rc.read_text())
            self.assertEqual(layout.read_text(), '[MainWindow]\nWidth=900\n')
            self.assertEqual(profile.read_text(), 'Font=Personal\nOpacity=.4\n')
            self.assertIn('State=serialized', saved[str(layout)])
            self.assertIn('Exec=konsole --hide-menubar --hide-tabbar --hide-toolbars', (home/'data/applications/org.kde.konsole.desktop').read_text())

    def test_kconfig_edit_is_idempotent_and_keeps_nested_groups(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'konsolerc'
            path.write_text('MenuBar=Disabled\n# comment\n[MainWindow][Toolbar sessionToolbar]\nVisible=Enabled\nOther=value\n')
            changes = {'MainWindow][Toolbar sessionToolbar': {'Visible': 'Disabled'}, 'New': {'Key': 'value'}}
            before = []
            setup.edit_ini(path, changes, lambda p: before.append(p.read_text()))
            first = path.read_text()
            setup.edit_ini(path, changes, lambda p: None)
            self.assertEqual(path.read_text(), first)
            self.assertIn('Other=value', first)
            self.assertIn('Visible=Enabled', before[0])
            self.assertEqual(setup.read_ini(path).get('New', 'Key'), 'value')

    def test_kde_install_backup_restore_roundtrip(self):
        self.kde_roundtrip(terminal_only=True)

    def test_full_install_launcher_and_restore(self):
        self.kde_roundtrip(terminal_only=False)

    def test_deferred_install_applies_without_opening_a_window(self):
        for terminal_only in (False, True):
            with self.subTest(terminal_only=terminal_only):
                self.kde_roundtrip(terminal_only=terminal_only, deferred=True)

    def kde_roundtrip(self, terminal_only, deferred=False):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            config = home / '.config'
            config.mkdir()
            rc = config / 'konsolerc'
            original = 'MenuBar=Disabled\n# keep root keys and comments\nRootKey=a=b\n[Desktop Entry]\nDefaultProfile=Personal.profile\n[Unrelated]\nKeep=hello\n'
            rc.write_text(original)
            kde_state = home / 'state/konsolestaterc'
            kde_state.parent.mkdir()
            kde_state.write_text('[MainWindow]\nState=old-toolbar-layout\nWidth=1200\n')
            shell = home / '.zshrc'
            shell.write_text('keep my shell\n')
            env = {'XDG_CONFIG_HOME': str(config), 'XDG_DATA_HOME': str(home / '.local/share'), 'XDG_STATE_HOME': str(home / 'state'), 'XDG_CURRENT_DESKTOP': 'KDE', 'XDG_SESSION_TYPE': 'wayland'}
            with patch.dict(os.environ, env), patch('pathlib.Path.home', return_value=home), \
                 patch('os.geteuid', return_value=1000), patch('shutil.which', side_effect=lambda n: '/usr/bin/' + n), \
                 patch('terminal_setup.preflight', return_value={'help': '--hide-toolbars'}), \
                 patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0)), \
                 patch('subprocess.Popen') as launch, patch('konsole_guard.running', return_value=False), \
                 patch('konsole_guard.wait_until_closed') as wait, \
                 patch('sys.argv', ['install.py', '--terminal', 'konsole'] + (['--terminal-only'] if terminal_only else []) + (['--wait-konsole'] if deferred else [])), contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(ROOT / 'install.py'), run_name='__main__')
                launch.assert_not_called()
                self.assertEqual(wait.call_count, int(deferred))
                self.assertEqual(setup.read_ini(rc).get('Unrelated', 'Keep'), 'hello')
                self.assertTrue(rc.read_text().startswith('MenuBar=Disabled\n# keep root keys and comments\nRootKey=a=b\n'))
                self.assertNotIn('__ungrouped__', rc.read_text())
                self.assertEqual(setup.read_ini(rc).get('KonsoleWindow', 'RemoveWindowTitleBarAndFrame'), 'true')
                if terminal_only:
                    self.assertEqual(shell.read_text(), 'keep my shell\n')
                else:
                    self.assertIn(' -e zsh', (home / '.local/bin/terminal-kit').read_text())
                    self.assertIn('Name=Terminal Kit', (home / '.local/share/applications/terminal-kit.desktop').read_text())
                profile = home / '.local/share/konsole/TerminalKit.profile'
                self.assertEqual(setup.read_ini(profile).get('Scrolling', 'ScrollBarPosition'), '2')
                backups = [p.parent for p in (home / '.local/state/manjaro-terminal-kit').glob('*/manifest.json')]
                self.assertEqual(len(backups), 1)
                manifest = json.loads((backups[0] / 'manifest.json').read_text())
                self.assertNotIn('State=', kde_state.read_text())
                self.assertIn('Width=1200', kde_state.read_text())
                self.assertFalse(manifest['properties'])
                self.assertEqual(manifest['terminal'], 'konsole')
                with patch('sys.argv', ['restore.py', '--backup', str(backups[0])]):
                    runpy.run_path(str(backups[0] / 'restore.py'), run_name='__main__')
                self.assertEqual(rc.read_text(), original)
                self.assertEqual(kde_state.read_text(), '[MainWindow]\nState=old-toolbar-layout\nWidth=1200\n')
                self.assertFalse(profile.exists())
                self.assertFalse((home / '.local/bin/terminal-kit').exists())
                self.assertFalse((home / '.local/share/applications/org.kde.konsole.desktop').exists())
                self.assertFalse((home / '.local/share/applications/terminal-kit.desktop').exists())
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
