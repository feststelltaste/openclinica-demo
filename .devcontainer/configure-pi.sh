#!/usr/bin/env bash
# Writes the Pi provider config from LLM_BASE_URL / LLM_API_KEY / LLM_MODEL.
# LLM_API is optional: openai-completions (default), openai-responses,
# anthropic-messages or google-generative-ai.
set -euo pipefail

if [[ -z "${LLM_BASE_URL:-}" || -z "${LLM_MODEL:-}" ]]; then
    echo "LLM_BASE_URL or LLM_MODEL not set; skipping Pi provider configuration."
    exit 0
fi

pi_dir="$HOME/.pi/agent"
mkdir -p "$pi_dir"

python3 - "$pi_dir" <<'PY'
import json, os, sys

pi_dir = sys.argv[1]
model = os.environ["LLM_MODEL"]
# Secrets arrive as env vars, so only reference them; a key typed in by hand
# (configure-llm.sh) is stored literally in the home directory.
api_key = os.environ["LLM_API_KEY"] if os.environ.get("PI_KEY_LITERAL") else "$LLM_API_KEY"

models = {
    "providers": {
        "llm": {
            "baseUrl": os.environ["LLM_BASE_URL"],
            "api": os.environ.get("LLM_API", "openai-completions"),
            "apiKey": api_key,
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
