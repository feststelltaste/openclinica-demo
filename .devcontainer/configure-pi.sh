#!/usr/bin/env bash
# Writes the Pi provider config from LITELLM_URL / LITELLM_API_KEY / LITELLM_MODEL.
# LITELLM_API is optional: openai-completions (default), openai-responses,
# anthropic-messages or google-generative-ai.
set -euo pipefail

if [[ -z "${LITELLM_URL:-}" || -z "${LITELLM_MODEL:-}" ]]; then
    echo "LITELLM_URL or LITELLM_MODEL not set; skipping Pi provider configuration."
    exit 0
fi

pi_dir="$HOME/.pi/agent"
mkdir -p "$pi_dir"

python3 - "$pi_dir" <<'PY'
import json, os, sys

pi_dir = sys.argv[1]
model = os.environ["LITELLM_MODEL"]
# Secrets arrive as env vars, so only reference them; a key typed in by hand
# (configure-llm.sh) is stored literally in the home directory.
api_key = os.environ["LITELLM_API_KEY"] if os.environ.get("PI_KEY_LITERAL") else "$LITELLM_API_KEY"

models = {
    "providers": {
        "litellm": {
            "baseUrl": os.environ["LITELLM_URL"],
            "api": os.environ.get("LITELLM_API", "openai-completions"),
            "apiKey": api_key,
            "models": [{"id": model, "name": model}],
        }
    }
}
settings_path = os.path.join(pi_dir, "settings.json")
settings = json.load(open(settings_path)) if os.path.exists(settings_path) else {}
settings.update({"defaultProvider": "litellm", "defaultModel": model})

json.dump(models, open(os.path.join(pi_dir, "models.json"), "w"), indent=2)
json.dump(settings, open(settings_path, "w"), indent=2)
PY
echo "Pi configured for $LITELLM_MODEL at $LITELLM_URL"
