"""Exercise dependency selection with fake package tools; never install real packages."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BootstrapTests(unittest.TestCase):
    def bootstrap(self, desktop, session, args=(), missing=True, cancel=False):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            log = path / 'calls'
            (path / 'pacman').write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALL_LOG"\n'
                                       + ('echo missing; exit 127\n' if missing else 'exit 0\n'))
            (path / 'sudo').write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALL_LOG"\n'
                                     + ('exit 1\n' if cancel else 'exit 0\n'))
            for tool in ['pacman', 'sudo']:
                (path / tool).chmod(0o755)
            env = dict(os.environ, PATH=str(path) + ':' + os.environ['PATH'], CALL_LOG=str(log),
                       XDG_CURRENT_DESKTOP=desktop, DESKTOP_SESSION='', XDG_SESSION_TYPE=session,
                       WAYLAND_DISPLAY='wayland-0' if session == 'wayland' else '')
            result = subprocess.run(['bash', str(ROOT / 'bootstrap.sh'), *args], env=env,
                                    capture_output=True, text=True)
            return result, log.read_text() if log.exists() else ''

    def test_kde_wayland_installs_matching_dependencies(self):
        result, calls = self.bootstrap('KDE', 'wayland')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('pacman -Syu --needed python fontconfig konsole', calls)
        self.assertIn('wl-clipboard', calls)
        self.assertNotIn('xfconf', calls)

    def test_xfce_x11(self):
        result, calls = self.bootstrap('XFCE', 'x11')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('xfce4-terminal xfconf', calls)
        self.assertIn('libxmu', calls)
        self.assertNotIn('wl-clipboard', calls)

    def test_gnome_terminal_only(self):
        result, calls = self.bootstrap('GNOME', 'wayland', ['--terminal-only'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('gnome-terminal glib2 dconf', calls)
        self.assertNotIn('zsh', calls)

    def test_check_and_help_never_install(self):
        for arg in ['--check', '--help']:
            result, calls = self.bootstrap('KDE', 'wayland', [arg])
            self.assertEqual(result.returncode, 0)
            self.assertEqual(calls, '')

    def test_installed_dependencies_do_not_upgrade(self):
        result, calls = self.bootstrap('KDE', 'wayland', missing=False)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('-Syu', calls)

    def test_cancel_stops_bootstrap(self):
        result, calls = self.bootstrap('KDE', 'wayland', cancel=True)
        self.assertNotEqual(result.returncode, 0)

    def test_override(self):
        result, calls = self.bootstrap('KDE', 'x11', ['--terminal', 'xfce4-terminal'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('xfce4-terminal xfconf', calls)
        self.assertNotIn('konsole', calls)
