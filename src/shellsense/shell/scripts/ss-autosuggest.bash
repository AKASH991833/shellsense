# ShellSense AI - Bash Auto-Suggestions
# Source this in your .bashrc: source ~/.shellsense/ss-autosuggest.bash

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

__shellsense_autosuggest() {
    local partial="${READLINE_LINE:0:READLINE_POINT}"
    local suggestion
    suggestion=$(__shellsense_get_suggestion "$partial" 2>/dev/null)
    if [[ -n "$suggestion" && "$suggestion" != "$partial" ]]; then
        local rest="${suggestion#$partial}"
        READLINE_LINE="${partial}${rest}"
        READLINE_POINT=${#READLINE_LINE}
    fi
}

# Bind Ctrl-Space to trigger autosuggest (like fish right-arrow accept)
bind -x '"\C-@": __shellsense_autosuggest'
# Also bind Ctrl-E for suggest-complete
bind -x '"\C-e": __shellsense_autosuggest'

# Show suggestion on prompt display via PROMPT_COMMAND
__shellsense_show_suggestion() {
    local last_cmd
    last_cmd=$(history 1 | sed 's/^ *[0-9]* *//')
    if [[ -n "$last_cmd" ]]; then
        local suggestion
        suggestion=$(__shellsense_get_suggestion "$last_cmd" 2>/dev/null)
        if [[ -n "$suggestion" && "$suggestion" != "$last_cmd" ]]; then
            local rest="${suggestion#$last_cmd}"
            if [[ -n "$rest" ]]; then
                echo -ne "\033[90m${rest}\033[0m"
            fi
        fi
    fi
}

# Add to PROMPT_COMMAND
if [[ -z "$PROMPT_COMMAND" ]]; then
    PROMPT_COMMAND="__shellsense_show_suggestion"
else
    PROMPT_COMMAND="__shellsense_show_suggestion;$PROMPT_COMMAND"
fi

# Also enable tab-completion integration
if type shellsense &>/dev/null; then
    eval "$(shellsense show-completion bash 2>/dev/null)"
fi
