#!/usr/bin/env bash
# Writes the Pi provider config from LITELLM_URL / LITELLM_API_KEY (any
# OpenAI-compatible gateway, for example LiteLLM or OpenRouter) and offers every
# model the key may use. LITELLM_MODEL is optional and selects the default model.
# LITELLM_API is optional: openai-completions (default), openai-responses,
# anthropic-messages or google-generative-ai.
# Alternatively set only OPENROUTER_API_KEY to use OpenRouter.
# OPENROUTER_PROVIDERS is optional: comma-separated OpenRouter provider slugs
# that requests are restricted to (default: cerebras, "any" = no restriction).
# OPENROUTER_FALLBACK=1 only prefers them and lets OpenRouter fall back to other
# providers if none of them can serve the request.
# LLM_PROVIDER is optional: litellm or openrouter, otherwise taken from the URL.
set -euo pipefail

# A Codespaces secret OPENROUTER_API_KEY alone is enough for OpenRouter. LLM_KEY_VAR
# names the environment variable that holds the key, so the config files can
# reference it instead of storing it.
export LLM_KEY_VAR=LITELLM_API_KEY
if [[ -z "${LITELLM_URL:-}" && -n "${OPENROUTER_API_KEY:-}" ]]; then
    export LITELLM_URL=https://openrouter.ai/api/v1
    export LITELLM_API_KEY="$OPENROUTER_API_KEY"
    export LLM_KEY_VAR=OPENROUTER_API_KEY
fi

if [[ -z "${LITELLM_URL:-}" ]]; then
    echo "LITELLM_URL or OPENROUTER_API_KEY not set; skipping Pi provider configuration."
    exit 0
fi

pi_dir="$HOME/.pi/agent"
mkdir -p "$pi_dir"

python3 - "$pi_dir" <<'PY'
import json, os, sys, urllib.request

pi_dir = sys.argv[1]
base = os.environ["LITELLM_URL"].rstrip("/")
key = os.environ.get("LITELLM_API_KEY", "")
provider = os.environ.get("LLM_PROVIDER") or ("openrouter" if "openrouter.ai" in base else "litellm")

# Fallback if the gateway cannot list its models: (id, name, context window).
MODELS = [
    ("eu.glm-53-flash", "GLM 5.3 Flash", 1310720),
    ("eu.deepseek-v4.1-flash", "DeepSeek V4.1 Flash", 1000000),
    ("eu.qwen3.8-flash-next", "Qwen 3.8 Flash Next", 262144),
]
# Secrets arrive as env vars, so only reference them; a key typed in by hand
# (setup.sh in the repository root) is stored literally in the home directory.
api_key = key if os.environ.get("PI_KEY_LITERAL") else "$" + os.environ["LLM_KEY_VAR"]


def get(url):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
    return json.load(urllib.request.urlopen(req, timeout=15))["data"]


def fetch(*urls):
    for url in urls:
        try:
            data = get(url)
        except Exception:
            continue
        if data:
            return data
    return []


def litellm_models():
    """Models the key may use, with limits from /model/info.

    Pi assumes 128000 / 16384 for models it does not know. LiteLLM only
    reports a limit if one is set for the model, so anything missing there
    keeps the value from the fallback list or Pi's default.
    """
    ids = [m["id"] for m in fetch(base + "/models")]
    info = {}
    for m in fetch(base + "/model/info", base.removesuffix("/v1") + "/model/info"):
        if "model_name" in m:
            info[m["model_name"]] = m.get("model_info") or {}
    known = {i: (n, c) for i, n, c in MODELS}
    out = []
    for i in ids or [m[0] for m in MODELS]:
        name, context = known.get(i, (i, None))
        e = {"id": i, "name": name}
        if context:
            e["contextWindow"] = context
        if info.get(i, {}).get("max_input_tokens"):
            e["contextWindow"] = info[i]["max_input_tokens"]
        if info.get(i, {}).get("max_output_tokens"):
            e["maxTokens"] = info[i]["max_output_tokens"]
        out.append(e)
    return out


def openrouter_models():
    # /models/user only lists what the account may use (privacy and provider
    # settings); /models is the whole catalogue.
    out = []
    for m in fetch(base + "/models/user", base + "/models"):
        e = {"id": m["id"], "name": m.get("name") or m["id"]}
        if m.get("context_length"):
            e["contextWindow"] = m["context_length"]
        if (m.get("top_provider") or {}).get("max_completion_tokens"):
            e["maxTokens"] = m["top_provider"]["max_completion_tokens"]
        out.append(e)
    return out


models_list = openrouter_models() if provider == "openrouter" else litellm_models()
if not models_list:
    models_list = [{"id": i, "name": n, "contextWindow": c} for i, n, c in MODELS]
ids = [m["id"] for m in models_list]

default = "qwen/qwen3.8-27b" if provider == "openrouter" else "eu.deepseek-v4.1-flash"
model = os.environ.get("LITELLM_MODEL") or default
if model not in ids:
    model = ids[0]

if provider == "openrouter":
    slugs = [p.strip() for p in (os.environ.get("OPENROUTER_PROVIDERS") or "cerebras").split(",") if p.strip()]
    if slugs != ["any"]:
        # Sent as the provider field of every request. Strict: a model that none
        # of the providers serves fails instead of going elsewhere.
        fallback = os.environ.get("OPENROUTER_FALLBACK") == "1"
        routing = {"order": slugs, "allow_fallbacks": True} if fallback else {"only": slugs, "allow_fallbacks": False}
        for m in models_list:
            m["compat"] = {"openRouterRouting": routing}
        # The providers may serve less context than the model offers (Cerebras
        # 64k of 1M), so take the limit from their endpoints of the default model.
        try:
            eps = json.load(urllib.request.urlopen(urllib.request.Request(
                base + "/models/" + model + "/endpoints",
                headers={"Authorization": "Bearer " + key}), timeout=15))["data"]["endpoints"]
        except Exception:
            eps = []
        ctx = [e["context_length"] for e in eps
               if (e.get("tag") or "").split("/")[0] in slugs and e.get("context_length")]
        if not ctx and not fallback:
            print(f"Warning: {model} is not offered by {', '.join(slugs)} on OpenRouter.")
        for m in models_list:
            if m["id"] == model and ctx and not fallback:
                m["contextWindow"] = min(ctx)
        print("OpenRouter providers: " + ", ".join(slugs) + (" (others as fallback)" if fallback else " only"))

models = {
    "providers": {
        "llm": {
            "baseUrl": os.environ["LITELLM_URL"],
            "api": os.environ.get("LITELLM_API", "openai-completions"),
            "apiKey": api_key,
            "models": models_list,
        }
    }
}
settings_path = os.path.join(pi_dir, "settings.json")
settings = json.load(open(settings_path)) if os.path.exists(settings_path) else {}
settings.update({"defaultProvider": "llm", "defaultModel": model})

json.dump(models, open(os.path.join(pi_dir, "models.json"), "w"), indent=2)
json.dump(settings, open(settings_path, "w"), indent=2)
print(f"{len(ids)} models, default: {model}")
PY
echo "Pi configured for $LITELLM_URL"
bash "$(dirname "$0")/configure-claude.sh"
[[ -n "${PI_SKIP_CHECK:-}" ]] || bash "$(dirname "$0")/check-llm.sh" || true
