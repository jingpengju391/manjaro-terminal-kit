#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
sha256sum --quiet -c SHA256SUMS
exec python3 install.py "$@"
