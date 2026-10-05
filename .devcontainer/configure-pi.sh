#!/usr/bin/env bash
# Writes the Pi provider config from LITELLM_URL / LITELLM_API_KEY / LITELLM_MODEL.
# LITELLM_MODEL is optional and selects the default model (first one below).
# LITELLM_API is optional: openai-completions (default), openai-responses,
# anthropic-messages or google-generative-ai.
set -euo pipefail

if [[ -z "${LITELLM_URL:-}" ]]; then
    echo "LITELLM_URL not set; skipping Pi provider configuration."
    exit 0
fi

pi_dir="$HOME/.pi/agent"
mkdir -p "$pi_dir"

python3 - "$pi_dir" <<'PY'
import json, os, sys

pi_dir = sys.argv[1]
MODELS = [
    ("eu.deepseek-v4.1-flash", "DeepSeek V4.1 Flash"),
    ("eu.glm-53-flash", "GLM 5.3 Flash"),
    ("eu.qwen3.8-flash-next", "Qwen 3.8 Flash Next"),
]
model = os.environ.get("LITELLM_MODEL") or MODELS[0][0]
# Secrets arrive as env vars, so only reference them; a key typed in by hand
# (configure-llm.sh) is stored literally in the home directory.
api_key = os.environ["LITELLM_API_KEY"] if os.environ.get("PI_KEY_LITERAL") else "$LITELLM_API_KEY"

models = {
    "providers": {
        "litellm": {
            "baseUrl": os.environ["LITELLM_URL"],
            "api": os.environ.get("LITELLM_API", "openai-completions"),
            "apiKey": api_key,
            "models": [{"id": i, "name": n} for i, n in MODELS],
        }
    }
}
settings_path = os.path.join(pi_dir, "settings.json")
settings = json.load(open(settings_path)) if os.path.exists(settings_path) else {}
settings.update({"defaultProvider": "litellm", "defaultModel": model})

json.dump(models, open(os.path.join(pi_dir, "models.json"), "w"), indent=2)
json.dump(settings, open(settings_path, "w"), indent=2)
PY
echo "Pi configured for $LITELLM_URL (default: ${LITELLM_MODEL:-eu.deepseek-v4.1-flash})"
[[ -n "${PI_SKIP_CHECK:-}" ]] || bash "$(dirname "$0")/check-llm.sh" || true
