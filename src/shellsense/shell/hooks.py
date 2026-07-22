from __future__ import annotations


def _get_bash_hooks() -> str:
    return """# ShellSense AI - Live Shell Autosuggestions
# True Fish-like inline suggestions with grey ghost text

__shellsense_get_suggestion() {
    local partial="$1"
    if [[ -z "$partial" || ! -S /tmp/shellsense-daemon.sock ]]; then
        echo ""
        return
    fi
    local request=$(printf '{"type":"suggest","partial":"%%s","limit":1}' "$partial")
    local response=$(echo "$request" | nc -U /tmp/shellsense-daemon.sock 2>/dev/null)
    if [[ -z "$response" ]]; then
        response=$(python3 -c "
import socket, json
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect('/tmp/shellsense-daemon.sock')
    s.sendall(b'$request')
    data = s.recv(65536)
    print(data.decode())
except:
    pass
s.close()
" 2>/dev/null)
    fi
    if [[ -n "$response" ]]; then
        python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    if d.get('success') and d.get('prediction'):
        print(d['prediction'])
except:
    pass
" <<< "$response" 2>/dev/null
    fi
}

# Show suggestion after prompt using grey text
__shellsense_show_suggestion() {
    local last_cmd=$(history 1 | sed 's/^ *[0-9]* *//')
    if [[ -z "$last_cmd" ]]; then
        return
    fi
    local suggestion=$(__shellsense_get_suggestion "$last_cmd")
    if [[ -n "$suggestion" && "$suggestion" != "$last_cmd" ]]; then
        local rest="${suggestion#$last_cmd}"
        if [[ -n "$rest" ]]; then
            echo -ne "\\033[90m${rest}\\033[0m"
        fi
    fi
}

# Accept suggestion at cursor (Ctrl-E / Ctrl-F)
__shellsense_accept_suggestion() {
    local suggestion=$(__shellsense_get_suggestion "$READLINE_LINE")
    if [[ -n "$suggestion" && "$suggestion" != "$READLINE_LINE" ]]; then
        READLINE_LINE="$suggestion"
        READLINE_POINT=${#READLINE_LINE}
    fi
}

# Error correction: if last command failed, suggest fix
__shellsense_error_correct() {
    local exit_code=$?
    if [[ $exit_code -eq 0 || -z "$__shellsense_last_cmd" ]]; then
        return
    fi
    local suggestion=$(__shellsense_get_suggestion "$__shellsense_last_cmd")
    if [[ -n "$suggestion" && "$suggestion" != "$__shellsense_last_cmd" ]]; then
        echo ""
        echo -e "\\033[31mShellSense:\\033[0m Did you mean: \\033[1m${suggestion}\\033[0m?"
        echo -ne "  Press \\033[1mCtrl-E\\033[0m to accept or \\033[1mCtrl-G\\033[0m to dismiss"
    fi
}

__shellsense_preexec() {
    __shellsense_last_cmd="$BASH_COMMAND"
    local warnings
    warnings=$(shellsense check-command "$BASH_COMMAND" 2>/dev/null)
    if [[ -n "$warnings" ]]; then
        echo "[ShellSense] Warning: $warnings" >&2
    fi
    if [[ -n "$BASH_COMMAND" && -S /tmp/shellsense-daemon.sock ]]; then
        local request=$(printf '{"type":"learn","command":"%%s"}' "$BASH_COMMAND")
        echo "$request" | nc -U /tmp/shellsense-daemon.sock 2>/dev/null &
    fi
}

# Ctrl+R fuzzy history search
__shellsense_history_search() {
    local partial="${READLINE_LINE:0:READLINE_POINT}"
    if [[ -z "$partial" ]]; then
        return
    fi
    local request=$(printf '{"type":"history_search","partial":"%%s","limit":10}' "$partial")
    local response=$(echo "$request" | nc -U /tmp/shellsense-daemon.sock 2>/dev/null)
    if [[ -z "$response" ]]; then
        response=$(python3 -c "
import socket, json
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect('/tmp/shellsense-daemon.sock')
    s.sendall(b'$request')
    data = s.recv(65536)
    print(data.decode())
except:
    pass
s.close()
" 2>/dev/null)
    fi
    if [[ -n "$response" ]]; then
        local pick=$(python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    if d.get('success') and d.get('results'):
        for r in d['results'][:5]:
            print(r.get('text', ''))
except:
    pass
" <<< "$response" 2>/dev/null | fzf --height=10 --prompt='history> ' 2>/dev/null)
        if [[ -n "$pick" ]]; then
            READLINE_LINE="$pick"
            READLINE_POINT=${#READLINE_LINE}
        fi
    fi
}

if [[ -z "$PROMPT_COMMAND" ]]; then
    PROMPT_COMMAND="__shellsense_show_suggestion"
else
    PROMPT_COMMAND="__shellsense_show_suggestion;$PROMPT_COMMAND"
fi

trap '__shellsense_preexec' DEBUG
trap '__shellsense_error_correct' ERR
bind -x '"\\C-e": __shellsense_accept_suggestion'
bind -x '"\\C-f": __shellsense_accept_suggestion'
bind -x '"\\C-r": __shellsense_history_search'
"""


def _get_zsh_hooks() -> str:
    return """# ShellSense AI - Zsh Autosuggestions
__shellsense_get_suggestion() {
    local partial="$1"
    if [[ -z "$partial" || ! -S /tmp/shellsense-daemon.sock ]]; then
        echo ""
        return
    fi
    local request=$(printf '{"type":"suggest","partial":"%%s","limit":1}' "$partial")
    local response=$(echo "$request" | nc -U /tmp/shellsense-daemon.sock 2>/dev/null)
    if [[ -z "$response" ]]; then
        response=$(python3 -c "
import socket, json
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect('/tmp/shellsense-daemon.sock')
    s.sendall(b'$request')
    data = s.recv(65536)
    print(data.decode())
except:
    pass
s.close()
" 2>/dev/null)
    fi
    if [[ -n "$response" ]]; then
        python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    if d.get('success') and d.get('prediction'):
        print(d['prediction'])
except:
    pass
" <<< "$response" 2>/dev/null
    fi
}

__shellsense_precmd_suggest() {
    if [[ -z "$BUFFER" ]]; then
        return
    fi
    local suggestion=$(__shellsense_get_suggestion "$BUFFER")
    if [[ -n "$suggestion" && "$suggestion" != "$BUFFER" ]]; then
        local rest="${suggestion#$BUFFER}"
        if [[ -n "$rest" ]]; then
            POSTDISPLAY="%F{cyan}${rest}%f"
        else
            POSTDISPLAY=""
        fi
    else
        POSTDISPLAY=""
    fi
}

__shellsense_accept_suggestion() {
    local suggestion=$(__shellsense_get_suggestion "$BUFFER")
    if [[ -n "$suggestion" && "$suggestion" != "$BUFFER" ]]; then
        BUFFER="$suggestion"
        CURSOR=${#BUFFER}
    fi
    POSTDISPLAY=""
}

__shellsense_error_correct() {
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        return
    fi
    local last_cmd=$(fc -ln -1)
    if [[ -z "$last_cmd" ]]; then
        return
    fi
    local suggestion=$(__shellsense_get_suggestion "$last_cmd")
    if [[ -n "$suggestion" && "$suggestion" != "$last_cmd" ]]; then
        echo ""
        echo "%F{red}ShellSense:%f Did you mean: %B${suggestion}%b?"
        echo "  Press %BCtrl-E%b to accept or %BCtrl-G%b to dismiss"
    fi
}

__shellsense_preexec() {
    local cmd="$1"
    local warnings
    warnings=$(shellsense check-command "$cmd" 2>/dev/null)
    if [[ -n "$warnings" ]]; then
        echo "[ShellSense] Warning: $warnings" >&2
    fi
    if [[ -n "$cmd" && -S /tmp/shellsense-daemon.sock ]]; then
        local request=$(printf '{"type":"learn","command":"%%s"}' "$cmd")
        echo "$request" | nc -U /tmp/shellsense-daemon.sock 2>/dev/null &
    fi
}

__shellsense_history_search() {
    local partial="$BUFFER"
    if [[ -z "$partial" ]]; then
        return
    fi
    local request=$(printf '{"type":"history_search","partial":"%%s","limit":10}' "$partial")
    local response=$(echo "$request" | nc -U /tmp/shellsense-daemon.sock 2>/dev/null)
    if [[ -z "$response" ]]; then
        response=$(python3 -c "
import socket, json
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect('/tmp/shellsense-daemon.sock')
    s.sendall(b'$request')
    data = s.recv(65536)
    print(data.decode())
except:
    pass
s.close()
" 2>/dev/null)
    fi
    if [[ -n "$response" ]]; then
        local pick=$(python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    if d.get('success') and d.get('results'):
        for r in d['results'][:5]:
            print(r.get('text', ''))
except:
    pass
" <<< "$response" 2>/dev/null | fzf --height=10 --prompt='history> ' 2>/dev/null)
        if [[ -n "$pick" ]]; then
            BUFFER="$pick"
            CURSOR=${#BUFFER}
        fi
    fi
}

precmd_functions+=(__shellsense_precmd_suggest)
preexec_functions+=(__shellsense_preexec)
zle -N __shellsense_accept_suggestion
zle -N __shellsense_history_search
bindkey '^E' __shellsense_accept_suggestion
bindkey '^F' __shellsense_accept_suggestion
bindkey '^R' __shellsense_history_search
"""


def _get_fish_hooks() -> str:
    return """# ShellSense AI - Fish Autosuggestions
function __shellsense_get_suggestion -a partial
    if test -z "$partial"; or not test -S /tmp/shellsense-daemon.sock
        return 1
    end
    set -l request (printf '{"type":"suggest","partial":"%%s","limit":1}' "$partial")
    set -l response (echo "$request" | nc -U /tmp/shellsense-daemon.sock 2>/dev/null)
    if test -z "$response"
        set -l response (python3 -c "
import socket, json
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect('/tmp/shellsense-daemon.sock')
    s.sendall(b'$request')
    data = s.recv(65536)
    print(data.decode())
except:
    pass
s.close()
" 2>/dev/null)
    end
    if test -n "$response"
        echo "$response" | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    if d.get('success') and d.get('prediction'):
        print(d['prediction'])
except:
    pass
" 2>/dev/null
    end
end

function __shellsense_preexec --on-event fish_preexec
    set -l cmd $argv[1]
    set -l warnings (shellsense check-command "$cmd" 2>/dev/null)
    if test -n "$warnings"
        echo "[ShellSense] Warning: $warnings" >&2
    end
    if test -n "$cmd"; and test -S /tmp/shellsense-daemon.sock
        set -l request (printf '{"type":"learn","command":"%%s"}' "$cmd")
        echo "$request" | nc -U /tmp/shellsense-daemon.sock 2>/dev/null &
    end
end

function __shellsense_accept_suggestion
    commandline -i (__shellsense_get_suggestion (commandline -p))
end

function __shellsense_history_search
    set -l partial (commandline -p)
    if test -z "$partial"
        return
    end
    set -l request (printf '{"type":"history_search","partial":"%%s","limit":10}' "$partial")
    set -l response (echo "$request" | nc -U /tmp/shellsense-daemon.sock 2>/dev/null)
    if test -n "$response"
        set -l pick (echo "$response" | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    if d.get('success') and d.get('results'):
        for r in d['results'][:5]:
            print(r.get('text', ''))
except:
    pass
" 2>/dev/null | fzf --height=10 --prompt='history> ' 2>/dev/null)
        if test -n "$pick"
            commandline -r "$pick"
        end
    end
end

bind \\ce __shellsense_accept_suggestion
bind \\cf __shellsense_accept_suggestion
bind \\cr __shellsense_history_search
"""


def get_hooks(shell: str) -> str:
    hooks = {
        "bash": _get_bash_hooks,
        "zsh": _get_zsh_hooks,
        "fish": _get_fish_hooks,
    }
    generator = hooks.get(shell)
    if generator:
        return generator()
    return ""


def get_prompt_snippet(shell: str) -> str:
    if shell == "bash":
        return 'PS1="\\[\\e[38;5;45m\\](shellsense)\\[\\e[0m\\] $PS1"'
    elif shell == "zsh":
        return 'PROMPT="%F{cyan}(shellsense)%f $PROMPT"'
    elif shell == "fish":
        return 'set -g fish_prompt "shellsense $fish_prompt"'
    return ""
