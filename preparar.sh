#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
uv_bin="${UV_BIN:-$HOME/.local/bin/uv}"
if command -v uv >/dev/null 2>&1; then uv_bin="$(command -v uv)"; fi
if [[ ! -x "$uv_bin" ]]; then
    echo 'Instale uv: https://docs.astral.sh/uv/getting-started/installation/'
    exit 1
fi
"$uv_bin" python install 3.12
"$uv_bin" venv --python 3.12 --allow-existing .venv
"$uv_bin" pip sync --python .venv/bin/python requirements.lock
".venv/bin/python" tools/prepare_assets.py
".venv/bin/python" tools/build_guide.py
echo 'Pronto. Execute ./jogar.sh.'
