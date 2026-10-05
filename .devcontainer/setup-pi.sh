#!/usr/bin/env bash
# Installs the Pi coding agent and points it at the LLM given by
# LLM_BASE_URL / LLM_API_KEY / LLM_MODEL (Codespaces secrets).
# LLM_API is optional: openai-completions (default), openai-responses,
# anthropic-messages or google-generative-ai.
set -euo pipefail

npm install -g --ignore-scripts @earendil-works/pi-coding-agent
pi install npm:pi-subagents

if [[ -z "${LLM_BASE_URL:-}" || -z "${LLM_MODEL:-}" ]]; then
    echo "LLM_BASE_URL or LLM_MODEL not set; skipping Pi provider configuration."
    exit 0
fi

pi_dir="$HOME/.pi/agent"
mkdir -p "$pi_dir"

# The API key stays out of the file: models.json only references $LLM_API_KEY.
python3 - "$pi_dir" <<'PY'
import json, os, sys

pi_dir = sys.argv[1]
model = os.environ["LLM_MODEL"]

models = {
    "providers": {
        "llm": {
            "baseUrl": os.environ["LLM_BASE_URL"],
            "api": os.environ.get("LLM_API", "openai-completions"),
            "apiKey": "$LLM_API_KEY",
            "models": [{"id": model, "name": model}],
        }
    }
}
settings_path = os.path.join(pi_dir, "settings.json")
settings = json.load(open(settings_path)) if os.path.exists(settings_path) else {}
settings.update({"defaultProvider": "llm", "defaultModel": model})

json.dump(models, open(os.path.join(pi_dir, "models.json"), "w"), indent=2)
json.dump(settings, open(settings_path, "w"), indent=2)
PY
echo "Pi configured for $LLM_MODEL at $LLM_BASE_URL"
