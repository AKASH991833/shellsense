# ShellSense AI - Zsh Auto-Suggestions
# Source this in your .zshrc: source ~/.shellsense/ss-autosuggest.zsh

__shellsense_daemon_socket="/tmp/shellsense-daemon.sock"

__shellsense_get_suggestion() {
    local partial="$1"
    if [[ -z "$partial" ]]; then
        echo ""
        return
    fi
    if [[ ! -S "$__shellsense_daemon_socket" ]]; then
        echo ""
        return
    fi
    local request
    request=$(printf '{"type":"suggest","partial":"%s","limit":1}' "$partial")
    local response
    response=$(echo "$request" | nc -U "$__shellsense_daemon_socket" 2>/dev/null)
    if [[ -z "$response" ]]; then
        response=$(python3 -c "
import socket, json
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect('$__shellsense_daemon_socket')
    s.sendall(b'$request')
    data = s.recv(65536)
    print(data.decode())
except: pass
s.close()
" 2>/dev/null)
    fi
    if [[ -n "$response" ]]; then
        local prediction
        prediction=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prediction',''))" 2>/dev/null)
        echo "$prediction"
    fi
}

# Zsh autosuggest widget
__shellsense_suggest_widget() {
    local partial="$BUFFER"
    local suggestion
    suggestion=$(__shellsense_get_suggestion "$partial" 2>/dev/null)
    if [[ -n "$suggestion" && "$suggestion" != "$partial" ]]; then
        local rest="${suggestion#$partial}"
        if [[ -n "$rest" ]]; then
            # Store suggestion for display
            POSTDISPLAY="$rest"
            zle -R
        fi
    else
        POSTDISPLAY=""
    fi
}

# Accept suggestion (Ctrl-E or Right)
__shellsense_accept_suggestion() {
    if [[ -n "$POSTDISPLAY" ]]; then
        BUFFER="$BUFFER$POSTDISPLAY"
        CURSOR=${#BUFFER}
        POSTDISPLAY=""
    fi
}

# Create zle widgets
zle -N __shellsense_suggest_widget
zle -N __shellsense_accept_suggestion

# Bind keys
bindkey '^E' __shellsense_accept_suggestion
bindkey '^F' __shellsense_accept_suggestion

# Auto-suggest on every keystroke (use with caution - may be slow)
# Uncomment the next line for real-time suggestions:
# zle -N self-insert __shellsense_suggest_widget

# Instead, suggest on partial word completion
zle -N backward-delete-char __shellsense_suggest_widget

# Better: integrate with zsh-autosuggestions if available
if typeset -f _zsh_autosuggest_strategy_match &>/dev/null; then
    ZSH_AUTOSUGGEST_STRATEGY=match
fi

# Show suggestion on precmd
__shellsense_precmd_suggest() {
    local last_cmd
    last_cmd=$(fc -ln -1 2>/dev/null | sed 's/^[[:space:]]*//')
    if [[ -n "$last_cmd" ]]; then
        local suggestion
        suggestion=$(__shellsense_get_suggestion "$last_cmd" 2>/dev/null)
        if [[ -n "$suggestion" && "$suggestion" != "$last_cmd" ]]; then
            local rest="${suggestion#$last_cmd}"
            if [[ -n "$rest" ]]; then
                print -Pn "%F{242}${rest}%f"
            fi
        fi
    fi
}
precmd_functions+=(__shellsense_precmd_suggest)

# Tab completion integration
if type ss &>/dev/null; then
    eval "$(ss show-completion zsh 2>/dev/null)"
fi
