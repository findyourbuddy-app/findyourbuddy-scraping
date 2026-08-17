#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -f .env ]; then
    echo ".env bulunamadi, .env.example'dan kopyalaniyor -- degerleri doldurmayi unutma" >&2
    cp .env.example .env
fi

uv sync
exec uv run python -m app.main
