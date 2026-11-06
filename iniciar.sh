#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -x .venv/bin/python ]]; then
    echo "Ambiente não encontrado. Primeiro execute ./preparar.sh."
    read -r -p "Pressione Enter para fechar..." _ || true
    exit 1
fi
exec ./jogar.sh "$@"
