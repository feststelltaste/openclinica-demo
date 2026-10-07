#!/usr/bin/env bash
# Installs the Pi coding agent and Claude Code if the image does not have them
# yet, adds the pi-subagents extension and, if LITELLM_URL is set (Codespaces
# secrets), configures both via configure-pi.sh. Failures of single steps are
# reported but do not stop the following ones.
set -uo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

# Offer to configure the agents in new terminals until done or skipped.
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    grep -qF prompt-llm.sh "$rc" 2>/dev/null ||
        echo "_oc_devcontainer_dir=\"$script_dir\"; . \"\$_oc_devcontainer_dir/prompt-llm.sh\"; unset _oc_devcontainer_dir" >> "$rc"
done

# JupyterLab runs without a login token and does not try to open a browser, so
# `jupyter lab` is enough and clicking port 8888 in the PORTS tab opens it. The
# port stays private to the owner of the codespace.
mkdir -p "$HOME/.jupyter"
cat > "$HOME/.jupyter/jupyter_server_config.py" <<'PY'
c.IdentityProvider.token = ""
c.ServerApp.open_browser = False
PY

# The global npm directory belongs to root in the image, so fall back to sudo.
npm_global() {
    npm install -g "$@" || sudo npm install -g "$@"
}

command -v pi >/dev/null ||
    npm_global --ignore-scripts @earendil-works/pi-coding-agent ||
    echo "Could not install Pi."
command -v claude >/dev/null ||
    npm_global @anthropic-ai/claude-code ||
    echo "Could not install Claude Code."

if command -v pi >/dev/null; then
    pi install npm:pi-subagents || echo "Could not install pi-subagents."
fi

bash "$script_dir/configure-pi.sh"
