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
# (id, name, context window). The windows are the figures published for the
# models; LiteLLM's /model/info takes precedence if it reports a limit.
MODELS = [
    ("eu.deepseek-v4.1-flash", "DeepSeek V4.1 Flash", 1000000),
    ("eu.glm-53-flash", "GLM 5.3 Flash", 1310720),
    ("eu.qwen3.8-flash-next", "Qwen 3.8 Flash Next", 262144),
]
model = os.environ.get("LITELLM_MODEL") or MODELS[0][0]
# Secrets arrive as env vars, so only reference them; a key typed in by hand
# (setup.sh) is stored literally in the home directory.
api_key = os.environ["LITELLM_API_KEY"] if os.environ.get("PI_KEY_LITERAL") else "$LITELLM_API_KEY"

def limits():
    """Context and output limits per model id from LiteLLM's /model/info.

    Pi assumes 128000 / 16384 for models it does not know. LiteLLM only
    reports a limit if one is set for the model, so anything missing there
    keeps Pi's default.
    """
    import urllib.request
    base = os.environ["LITELLM_URL"].rstrip("/")
    key = os.environ.get("LITELLM_API_KEY", "")
    for url in (base + "/model/info", base.removesuffix("/v1") + "/model/info"):
        try:
            req = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
            data = json.load(urllib.request.urlopen(req, timeout=10))["data"]
        except Exception:
            continue
        found = {m["model_name"]: m.get("model_info") or {} for m in data if "model_name" in m}
        if found:
            return found
    return {}


info = limits()


def entry(model_id, name, context):
    e = {"id": model_id, "name": name, "contextWindow": context}
    i = info.get(model_id, {})
    if i.get("max_input_tokens"):
        e["contextWindow"] = i["max_input_tokens"]
    if i.get("max_output_tokens"):
        e["maxTokens"] = i["max_output_tokens"]
    return e


models = {
    "providers": {
        "litellm": {
            "baseUrl": os.environ["LITELLM_URL"],
            "api": os.environ.get("LITELLM_API", "openai-completions"),
            "apiKey": api_key,
            "models": [entry(i, n, c) for i, n, c in MODELS],
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
bash "$(dirname "$0")/configure-claude.sh"
[[ -n "${PI_SKIP_CHECK:-}" ]] || bash "$(dirname "$0")/check-llm.sh" || true
