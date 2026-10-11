# Shell dispatcher for pi-worktree-extension: `pi -w <name>` opens (or creates)
# a task worktree and resumes its latest Pi session; everything else goes to
# the real Pi. Sourced from ~/.bashrc by setup-pi.sh.
PI_WORKTREE_REAL_PI="${PI_WORKTREE_REAL_PI:-$(type -P pi)}"
export PI_WORKTREE_REAL_PI
export PI_WORKTREE_LAUNCHER="$HOME/.pi/agent/npm/node_modules/.bin/pi-worktree"

pi() {
    case "${1-}" in
        -w|--worktree)
            if (($# < 2)); then
                echo "usage: pi -w <name> [Pi args...]" >&2
                return 2
            fi
            shift
            command "$PI_WORKTREE_LAUNCHER" "$@"
            ;;
        *)
            command "$PI_WORKTREE_REAL_PI" "$@"
            ;;
    esac
}
