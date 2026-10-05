#!/usr/bin/env bash
# Installs the Pi coding agent and, if LITELLM_URL is set
# (Codespaces secrets), configures it via configure-pi.sh.
set -euo pipefail

npm install -g --ignore-scripts @earendil-works/pi-coding-agent
pi install npm:pi-subagents

bash "$(dirname "$0")/configure-pi.sh"
