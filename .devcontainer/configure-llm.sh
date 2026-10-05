#!/usr/bin/env bash
# Workshop helper: asks for the LLM endpoint and key and configures Pi.
# Run once in the Codespace terminal:  bash .devcontainer/configure-llm.sh
set -euo pipefail

read -r -p "LiteLLM URL: " LITELLM_URL
read -r -s -p "LiteLLM API key (input hidden): " LITELLM_API_KEY
echo
read -r -p "Default model id [eu.deepseek-v4.1-flash]: " LITELLM_MODEL
LITELLM_MODEL="${LITELLM_MODEL:-eu.deepseek-v4.1-flash}"

export LITELLM_URL LITELLM_API_KEY LITELLM_MODEL PI_KEY_LITERAL=1
bash "$(dirname "$0")/configure-pi.sh"
echo "Start the agent with: pi"
