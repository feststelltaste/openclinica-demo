#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
compose_file="${COMPOSE_FILE:-$repo_dir/docker/docker-compose.test.yml}"
generator="$repo_dir/docker/demo/generate_demo_sql.py"

if [[ "${1:-}" != "--yes" ]]; then
    echo "This deletes the local test database and loads fresh synthetic demo data."
    echo "Re-run with: $0 --yes"
    exit 2
fi

source "$repo_dir/docker/demo/base-url.sh"
compose=(docker compose -f "$compose_file")

"${compose[@]}" down --volumes
"${compose[@]}" up -d

echo "Waiting for OpenClinica to create and migrate the database..."
for attempt in $(seq 1 36); do
    status="$("${compose[@]}" ps --format json openclinica 2>/dev/null || true)"
    if [[ "$status" == *'"Health":"healthy"'* ]]; then
        break
    fi
    if [[ "$attempt" -eq 36 ]]; then
        echo "OpenClinica did not become healthy in time." >&2
        exit 1
    fi
    sleep 5
done

"${compose[@]}" stop openclinica
python3 "$generator" |
    "${compose[@]}" exec -T database \
        psql --quiet -U clinica -d openclinica -v ON_ERROR_STOP=1
"${compose[@]}" start openclinica

echo "Loaded 8 demo studies and 160 synthetic subjects."
bash "$repo_dir/docker/demo/print-url.sh"
