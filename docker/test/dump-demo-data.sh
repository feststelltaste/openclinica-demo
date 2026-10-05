#!/usr/bin/env bash
# Writes the migrated database with the demo data to a gzipped SQL file.
# Run after reset-demo-data.sh. Usage: dump-demo-data.sh <output.sql.gz>
set -euo pipefail

repo_dir="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
compose_file="${COMPOSE_FILE:-$repo_dir/docker-compose.test.yml}"
output="${1:?usage: $0 <output.sql.gz>}"
compose=(docker compose -f "$compose_file")

# reset-demo-data.sh returns while OpenClinica is still starting and may hold
# the Liquibase lock. Wait until it is up, then stop it so nothing writes.
for attempt in $(seq 1 36); do
    status="$("${compose[@]}" ps --format json openclinica 2>/dev/null || true)"
    [[ "$status" == *'"Health":"healthy"'* ]] && break
    if [[ "$attempt" -eq 36 ]]; then
        echo "OpenClinica did not become healthy in time." >&2
        exit 1
    fi
    sleep 5
done
"${compose[@]}" stop openclinica

"${compose[@]}" exec -T database \
    pg_dump -U clinica --no-owner --no-privileges openclinica | gzip > "$output"
ls -lh "$output"
