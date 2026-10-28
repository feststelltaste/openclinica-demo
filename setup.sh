#!/usr/bin/env bash
# Workshop helper: asks for the URL and key of an OpenAI-compatible gateway
# (LiteLLM or OpenRouter), configures Pi and Claude Code with every model the
# key may use and checks that the key works. Run in the Codespace terminal:
#   ./setup.sh
set -euo pipefail

dir="$(CDPATH= cd -- "$(dirname -- "$0")/.devcontainer" && pwd)"

# Values from the environment (Codespaces secrets) are used on the first
# round; anything missing is asked for, and so is everything after a failure.
LITELLM_URL="${LITELLM_URL:-}"
LITELLM_API_KEY="${LITELLM_API_KEY:-}"
if [[ -z "$LITELLM_URL" && -n "${OPENROUTER_API_KEY:-}" ]]; then
    LITELLM_URL=https://openrouter.ai/api/v1
    LITELLM_API_KEY="$OPENROUTER_API_KEY"
    echo "Using OpenRouter with OPENROUTER_API_KEY from the environment."
fi

while true; do
    if [[ -z "$LITELLM_URL" ]]; then
        read -r -p "LLM URL (e.g. https://openrouter.ai/api/v1): " LITELLM_URL
    fi
    if [[ -z "$LITELLM_API_KEY" ]]; then
        read -r -s -p "LLM API key: " LITELLM_API_KEY
        echo
    fi
    read -r -p "Default model id (Enter = default of the provider): " LITELLM_MODEL

    PI_SKIP_CHECK=1 PI_KEY_LITERAL=1 LITELLM_URL="$LITELLM_URL" LITELLM_API_KEY="$LITELLM_API_KEY" \
        LITELLM_MODEL="${LITELLM_MODEL:-}" bash "$dir/configure-pi.sh"

    if bash "$dir/check-llm.sh"; then
        break
    fi
    read -r -p "Enter the values again? [Y/n] " again
    [[ "$again" =~ ^[nN] ]] && break
    LITELLM_URL=
    LITELLM_API_KEY=
done
echo "Start an agent with: pi  or  claude"
