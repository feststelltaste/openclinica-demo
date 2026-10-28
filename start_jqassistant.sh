#!/usr/bin/env bash
# Starts the jQAssistant server (Neo4j browser on 7474, Bolt on 7687) on the
# store from the last "mvn verify" and prints the URLs to open. Run in the
# Codespace terminal:
#   ./start_jqassistant.sh
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -d target/jqassistant/store ]]; then
    echo "No jQAssistant store found, it is created by 'mvn verify -DskipTests'."
    read -r -p "Run it now? [Y/n] " answer
    if [[ "${answer,,}" == n* ]]; then
        exit 1
    fi
    mvn --batch-mode verify -DskipTests
fi

if [[ -n "${CODESPACE_NAME:-}" ]]; then
    domain="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
    cat <<EOF
Open   https://${CODESPACE_NAME}-7474.${domain}/index.html
Connect to bolt+s://${CODESPACE_NAME}-7687.${domain}:443 with "No authentication"
(add ports 7474 and 7687 in the Ports tab if they are missing)
EOF
else
    echo "Open http://localhost:7474/index.html and connect to bolt://localhost:7687"
fi

exec mvn --batch-mode jqassistant:server
