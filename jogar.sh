#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -x .venv/bin/python ]]; then
    echo 'Ambiente ausente. Execute ./preparar.sh primeiro.'
    exit 1
fi
exec .venv/bin/python main.py "$@"
