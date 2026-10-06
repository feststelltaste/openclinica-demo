#!/usr/bin/env bash
# Installs the Pi coding agent (and Claude Code if missing) and, if LITELLM_URL is set
# (Codespaces secrets), configures it via configure-pi.sh.
set -euo pipefail

# Pi itself is part of the dev container image; install it only if missing.
command -v pi >/dev/null || npm install -g --ignore-scripts @earendil-works/pi-coding-agent
command -v claude >/dev/null || npm install -g @anthropic-ai/claude-code
pi install npm:pi-subagents

# Offer to configure Pi in new terminals until it is configured or skipped.
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    grep -qF prompt-llm.sh "$rc" 2>/dev/null ||
        echo "_oc_devcontainer_dir=\"$script_dir\"; . \"\$_oc_devcontainer_dir/prompt-llm.sh\"; unset _oc_devcontainer_dir" >> "$rc"
done

bash "$script_dir/configure-pi.sh"
