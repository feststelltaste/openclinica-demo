#!/usr/bin/env bash
# Developer helper: builds the WAR and (re)starts OpenClinica with the
# docker-compose.test.yml stack (plain Tomcat + mounted WAR).
#   docker/rebuild.sh          build + restart
#   docker/rebuild.sh --no-build   restart only
set -euo pipefail

docker_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
repo_dir="$(dirname "$docker_dir")"
compose=(docker compose -f "$docker_dir/docker-compose.test.yml")

source "$docker_dir/demo/base-url.sh"

if [[ "${1:-}" != "--no-build" ]]; then
    (cd "$repo_dir" && mvn -B -DskipTests package)
fi

# "up -d" starts the stack on the first run. --force-recreate makes the
# container pick up the new WAR file (a single-file bind mount keeps the old
# inode when Maven replaces the file).
"${compose[@]}" up -d --force-recreate openclinica

echo "Waiting for OpenClinica (takes 1-2 minutes) ..."
for _ in $(seq 1 60); do
    if curl -fsS http://localhost:8080/OpenClinica/pages/login/login >/dev/null 2>&1; then
        bash "$docker_dir/demo/print-url.sh"
        exit 0
    fi
    sleep 5
done
echo "OpenClinica did not become ready. Logs: ${compose[*]} logs openclinica" >&2
exit 1
