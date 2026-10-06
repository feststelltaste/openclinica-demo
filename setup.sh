#!/usr/bin/env bash
# Workshop helper: asks for the LiteLLM endpoint and key, configures Pi and
# checks that the key works. Run in the Codespace terminal:
#   ./setup.sh
set -euo pipefail

dir="$(CDPATH= cd -- "$(dirname -- "$0")/.devcontainer" && pwd)"

while true; do
    read -r -p "LiteLLM URL: " LITELLM_URL
    read -r -p "LiteLLM API key: " LITELLM_API_KEY
    read -r -p "Default model id [eu.glm-53-flash]: " LITELLM_MODEL
    LITELLM_MODEL="${LITELLM_MODEL:-eu.glm-53-flash}"

    PI_SKIP_CHECK=1 PI_KEY_LITERAL=1 LITELLM_URL="$LITELLM_URL" LITELLM_API_KEY="$LITELLM_API_KEY" \
        LITELLM_MODEL="$LITELLM_MODEL" bash "$dir/configure-pi.sh"

    if bash "$dir/check-llm.sh"; then
        break
    fi
    read -r -p "Enter the values again? [Y/n] " again
    [[ "$again" =~ ^[nN] ]] && break
done
echo "Start an agent with: pi  or  claude"
