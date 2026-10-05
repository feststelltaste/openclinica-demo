#!/usr/bin/env bash
# Workshop helper: asks for the LLM endpoint and key and configures Pi.
# Run once in the Codespace terminal:  bash .devcontainer/configure-llm.sh
set -euo pipefail

read -r -p "LLM base URL: " LLM_BASE_URL
read -r -s -p "LLM API key (input hidden): " LLM_API_KEY
echo
read -r -p "Model id: " LLM_MODEL

export LLM_BASE_URL LLM_API_KEY LLM_MODEL PI_KEY_LITERAL=1
bash "$(dirname "$0")/configure-pi.sh"
echo "Start the agent with: pi"
