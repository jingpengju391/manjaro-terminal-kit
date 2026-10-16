#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
sha256sum --quiet -c SHA256SUMS
bash bootstrap.sh "$@"
# Validate the system interpreter before changing user configuration.
if ! command -v python3 >/dev/null; then
  echo '缺少 Python。请先执行 sudo pacman -Syu python，再重试。' >&2
  exit 1
fi
if ! python3 -c 'import argparse, datetime, json, os, platform, shutil, subprocess, math; from pathlib import Path'; then
  cat >&2 <<'MESSAGE'
系统 Python 无法正常加载；安装尚未开始，配置未修改。
如果上方出现 GLIBC_x.xx not found，说明系统 Python 和 glibc 不匹配。
在目标 Manjaro 电脑执行完整升级并重装这两个包：
  sudo pacman -Syu glibc python
完成后重新启动电脑，再运行：
  python3 -c 'import math; print("Python OK")'
不要从其他电脑复制 libm.so.6/libc.so.6，也不要手动替换系统库。
MESSAGE
  exit 1
fi
exec python3 install.py "$@"
