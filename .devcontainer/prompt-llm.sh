# Sourced from ~/.bashrc and ~/.zshrc (see setup-pi.sh), which sets
# _oc_devcontainer_dir to this folder. In an interactive
# terminal it offers to configure Pi for LiteLLM until that has been done or
# skipped. Skip with "s"; run `./setup.sh` any time.
case $- in *i*) ;; *) return 0 2>/dev/null ;; esac
[ -t 0 ] && [ -t 1 ] || return 0
# Secrets are set: setup-pi.sh configures Pi itself, nothing to ask.
[ -n "${LITELLM_URL:-}" ] && return 0

_llm_dir="${HOME}/.pi"
if [ ! -f "${_llm_dir}/agent/models.json" ] && [ ! -f "${_llm_dir}/llm-prompt-skipped" ]; then
    printf '\nPi is not connected to LiteLLM yet.\n'
    printf 'Press Enter to enter URL and API key now, or type s to skip: '
    read -r _llm_answer
    case "$_llm_answer" in
        s|S|skip)
            mkdir -p "$_llm_dir" && : > "${_llm_dir}/llm-prompt-skipped"
            printf 'Skipped. Run: ./setup.sh\n\n'
            ;;
        *)
            bash "${_oc_devcontainer_dir}/../setup.sh"
            ;;
    esac
    unset _llm_answer
fi
unset _llm_dir
