#!/usr/bin/env bash
# Called by install.sh before Python. No settings are changed here.
set -euo pipefail
terminal=auto
terminal_only=false
check=false
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  case "${args[i]}" in
    --check|--help|-h) check=true ;;
    --terminal-only) terminal_only=true ;;
    --terminal=*) terminal=${args[i]#*=} ;;
    --terminal)
      ((i+=1))
      terminal=${args[i]:-invalid}
      ;;
    --vscode) ;;
    *) exit 0 ;; # Let argparse explain invalid arguments before any package installation.
  esac
done
[[ $check == true ]] && exit 0
if [[ $EUID == 0 ]]; then
  echo '请用普通桌面用户运行 bash install.sh，不要 sudo。' >&2
  exit 1
fi
if [[ $(uname -m) != x86_64 ]]; then
  echo "此工具包仅支持 x86_64；未修改系统。" >&2
  exit 1
fi
if [[ $terminal == auto ]]; then
  desktop="${XDG_CURRENT_DESKTOP:-}:${DESKTOP_SESSION:-}"
  case "${desktop,,}" in
    *kde*|*plasma*) terminal=konsole ;;
    *xfce*) terminal=xfce4-terminal ;;
    *gnome*) terminal=gnome-terminal ;;
    *) exit 0 ;; # Python handles unknown/ambiguous desktops without guessing.
  esac
fi
packages=(python fontconfig)
case "$terminal" in
  konsole) packages+=(konsole) ;;
  xfce4-terminal) packages+=(xfce4-terminal xfconf) ;;
  gnome-terminal) packages+=(gnome-terminal glib2 dconf) ;;
  *) exit 0 ;;
esac
if [[ $terminal_only == false ]]; then
  packages+=(zsh manjaro-zsh-config zsh-autosuggestions zsh-syntax-highlighting)
  if [[ ${XDG_SESSION_TYPE:-} == wayland || -n ${WAYLAND_DISPLAY:-} ]]; then
    packages+=(wl-clipboard)
  else
    packages+=(libxmu)
  fi
fi
if ! command -v pacman >/dev/null; then
  echo '自动安装依赖仅支持使用 pacman 的 Manjaro；未修改系统。' >&2
  exit 1
fi
# pacman -T exits 127 when dependencies are missing, 0 when satisfied.
status=0
missing=$(pacman -T "${packages[@]}") || status=$?
if [[ $status != 0 && $status != 127 ]]; then
  echo '无法检查系统依赖，已停止。' >&2
  exit "$status"
fi
if [[ -n $missing ]]; then
  printf '目标终端：%s\n缺少依赖：\n%s\n' "$terminal" "$missing"
  echo '将通过 pacman 完整升级系统并补齐依赖；请查看 pacman 的确认提示。取消后不会写入终端配置。'
  sudo pacman -Syu --needed "${packages[@]}"
fi
