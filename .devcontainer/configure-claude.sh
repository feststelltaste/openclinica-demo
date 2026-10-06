#!/usr/bin/env bash
# Points Claude Code at LiteLLM (its Anthropic-compatible /v1/messages API).
# Called by configure-pi.sh with the same LITELLM_* variables. The three
# models fill Claude Code's model slots: Sonnet = DeepSeek (default), Opus = GLM,
# Haiku (background tasks) = Qwen.
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


deepseek, glm, qwen = "eu.deepseek-v4.1-flash", "eu.glm-53-flash", "eu.qwen3.8-flash-next"
default = os.environ.get("LITELLM_MODEL") or deepseek

settings = load(settings_path)
env = settings.setdefault("env", {})
env.update({
    # Claude Code adds /v1/messages itself, so the OpenAI-style /v1 must go.
    "ANTHROPIC_BASE_URL": os.environ["LITELLM_URL"].rstrip("/").removesuffix("/v1"),
    "ANTHROPIC_MODEL": default,
    "ANTHROPIC_DEFAULT_SONNET_MODEL": deepseek,
    "ANTHROPIC_DEFAULT_OPUS_MODEL": glm,
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": qwen,
    "CLAUDE_CODE_SUBAGENT_MODEL": default,
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1",
})
if os.environ.get("PI_KEY_LITERAL"):
    # Key typed in by hand: it lives only in this file in the home directory.
    env["ANTHROPIC_AUTH_TOKEN"] = os.environ["LITELLM_API_KEY"]
    settings.pop("apiKeyHelper", None)
else:
    # Key from a Codespaces secret: read it from the environment when needed.
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    settings["apiKeyHelper"] = 'printf %s "$LITELLM_API_KEY"'

json.dump(settings, open(settings_path, "w"), indent=2)
os.chmod(settings_path, 0o600)

# Skip the first-run onboarding (login, theme) because the gateway is set up.
state = load(state_path)
state["hasCompletedOnboarding"] = True
json.dump(state, open(state_path, "w"), indent=2)
PY
echo "Claude Code configured (default: ${LITELLM_MODEL:-eu.deepseek-v4.1-flash})"
