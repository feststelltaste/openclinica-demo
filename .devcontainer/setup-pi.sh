#!/usr/bin/env bash
# Installs the Pi coding agent and Claude Code if the image does not have them
# yet, adds the pi-subagents extension and, if LITELLM_URL is set (Codespaces
# secrets), configures both via configure-pi.sh. Without the secrets, the
# participants run ./setup.sh themselves. Failures of single steps are
# reported but do not stop the following ones.
set -uo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

# JupyterLab runs without a login token and does not try to open a browser, so
# `jupyter lab` is enough and clicking port 8888 in the PORTS tab opens it. The
# port stays private to the owner of the codespace.
mkdir -p "$HOME/.jupyter"
cat > "$HOME/.jupyter/jupyter_server_config.py" <<'PY'
c.IdentityProvider.token = ""
c.ServerApp.open_browser = False
PY

# The global npm directory belongs to root in the image, so fall back to sudo.
# Every network step is bounded and gets no stdin, so a stuck download or an
# interactive prompt cannot block the codespace creation (and with it the
# postStartCommand that starts OpenClinica).
npm_global() {
    timeout 180 npm install -g "$@" </dev/null ||
        timeout 180 sudo -n npm install -g "$@" </dev/null
}

command -v pi >/dev/null ||
    npm_global --ignore-scripts @earendil-works/pi-coding-agent ||
    echo "Could not install Pi."
command -v claude >/dev/null ||
    npm_global @anthropic-ai/claude-code ||
    echo "Could not install Claude Code."

if command -v pi >/dev/null; then
    timeout 120 pi install npm:pi-subagents </dev/null || echo "Could not install pi-subagents."
fi

bash "$script_dir/configure-pi.sh"
