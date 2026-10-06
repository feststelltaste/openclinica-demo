# Source this file: exports OC_BASE_URL (public URL of the Tomcat root).
if [[ -n "${CODESPACE_NAME:-}" ]]; then
    export OC_BASE_URL="https://${CODESPACE_NAME}-8080.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
else
    export OC_BASE_URL="${OC_BASE_URL:-http://127.0.0.1:8080}"
fi
