#!/usr/bin/env bash
# Checks that the LLM URL and API key in the Pi configuration work.
# Exit code: 0 = valid, 1 = key rejected, 2 = unreachable or other error,
# 3 = not configured.
set -uo pipefail

models_json="$HOME/.pi/agent/models.json"
settings_json="$HOME/.pi/agent/settings.json"
[[ -f "$models_json" ]] || { echo "Pi is not configured yet."; exit 3; }

# Prints base URL, API key and default model on three lines; the key is
# resolved from the environment if models.json only references it.
mapfile -t cfg < <(python3 - "$models_json" "$settings_json" <<'PY'
import json, os, sys
p = next(iter(json.load(open(sys.argv[1]))["providers"].values()))
key = p["apiKey"]
if key.startswith("$"):
    key = os.environ.get(key[1:].strip("{}"), "")
try:
    model = json.load(open(sys.argv[2])).get("defaultModel", "")
except OSError:
    model = ""
print(p["baseUrl"].rstrip("/")); print(key); print(model)
print(",".join(m["id"] for m in p.get("models", [])))
PY
)
base_url="${cfg[0]:-}"; api_key="${cfg[1]:-}"; model="${cfg[2]:-}"

# OpenRouter lists its models without a key, so /models says nothing about the
# key; its /auth/key answers 401 for a bad one.
openrouter=
[[ "${LLM_PROVIDER:-}" == openrouter || "$base_url" == *openrouter.ai* ]] && openrouter=1
endpoint=models
[[ -n "$openrouter" ]] && endpoint=auth/key

if [[ -z "$api_key" ]]; then
    echo "No API key available (LITELLM_API_KEY is not set)."
    exit 1
fi

body="$(mktemp)"; trap 'rm -f "$body"' EXIT
# The key goes through stdin so it does not show up in the process list.
status="$(printf 'header = "Authorization: Bearer %s"\n' "$api_key" |
    curl -sS -K - -m 15 -o "$body" -w '%{http_code}' "$base_url/$endpoint" 2>/dev/null)" || status=000

case "$status" in
    200)
        if [[ -z "$openrouter" && -n "$model" ]] && ! grep -qF "\"$model\"" "$body"; then
            echo "API key is valid, but the model $model is not available for it."
            exit 2
        fi
        echo "API key is valid${model:+ (default model: $model)}."
        ;;
    401|403) echo "API key was rejected (HTTP $status)."; exit 1 ;;
    000)     echo "Could not reach $base_url."; exit 2 ;;
    *)       echo "Unexpected answer from $base_url/$endpoint (HTTP $status)."; exit 2 ;;
esac
