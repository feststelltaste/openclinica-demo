#!/usr/bin/env bash
# Points Claude Code at LiteLLM or OpenRouter (their Anthropic-compatible
# /v1/messages API). Called by configure-pi.sh with the same LITELLM_* variables.
# Every model slot (Sonnet, Opus, Haiku, Fable) and every background model uses
# the default model: Qwen Flash on LiteLLM, qwen/qwen3.8-27b on OpenRouter.
# All of them are pinned, because an unpinned one would ask for a real Claude
# model, which OpenRouter serves and bills.
set -euo pipefail

mkdir -p "$HOME/.claude"

python3 <<'PY'
import json, os

home = os.path.expanduser("~")
settings_path = os.path.join(home, ".claude", "settings.json")
state_path = os.path.join(home, ".claude.json")


def load(path):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return {}


openrouter = (os.environ.get("LLM_PROVIDER") or
              ("openrouter" if "openrouter.ai" in os.environ["LITELLM_URL"] else "litellm")) == "openrouter"
default = os.environ.get("LITELLM_MODEL") or ("qwen/qwen3.8-27b" if openrouter else "eu.qwen3.8-flash-next")

settings = load(settings_path)
env = settings.setdefault("env", {})
env.update({
    # Claude Code adds /v1/messages itself, so the OpenAI-style /v1 must go.
    "ANTHROPIC_BASE_URL": os.environ["LITELLM_URL"].rstrip("/").removesuffix("/v1"),
    "ANTHROPIC_MODEL": default,
    "ANTHROPIC_DEFAULT_SONNET_MODEL": default,
    "ANTHROPIC_DEFAULT_OPUS_MODEL": default,
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": default,
    "ANTHROPIC_DEFAULT_FABLE_MODEL": default,
    "ANTHROPIC_SMALL_FAST_MODEL": default,
    "CLAUDE_CODE_AUTO_MODE_MODEL": default,
    "CLAUDE_CODE_BG_CLASSIFIER_MODEL": default,
    "CLAUDE_CODE_SUBAGENT_MODEL": default,
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1",
    # Claude Code is installed globally in the container; no self-update.
    "DISABLE_AUTOUPDATER": "1",
    "DISABLE_TELEMETRY": "1",
    "DISABLE_ERROR_REPORTING": "1",
})
if openrouter:
    # OpenRouter wants the key as auth token and an explicitly empty API key.
    env["ANTHROPIC_API_KEY"] = ""
else:
    env.pop("ANTHROPIC_API_KEY", None)
settings["includeCoAuthoredBy"] = False
settings["autoUpdates"] = False
if os.environ.get("PI_KEY_LITERAL"):
    # Key typed in by hand: it lives only in this file in the home directory.
    env["ANTHROPIC_AUTH_TOKEN"] = os.environ["LITELLM_API_KEY"]
    settings.pop("apiKeyHelper", None)
else:
    # Key from a Codespaces secret: read it from the environment when needed.
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    settings["apiKeyHelper"] = 'printf %s "$' + os.environ.get("LLM_KEY_VAR", "LITELLM_API_KEY") + '"'

json.dump(settings, open(settings_path, "w"), indent=2)
os.chmod(settings_path, 0o600)

# Skip the first-run onboarding (login, theme) because the gateway is set up.
state = load(state_path)
state["hasCompletedOnboarding"] = True
state.setdefault("theme", "light")
json.dump(state, open(state_path, "w"), indent=2)
PY
echo "Claude Code configured for $LITELLM_URL"
