from __future__ import annotations


def _get_bash_hooks() -> str:
    return """# ShellSense AI - Live Shell Autosuggestions
# Like Fish shell - shows ghost text suggestions inline

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

__shellsense_accept_suggestion() {
    local suggestion=$(__shellsense_get_suggestion "$READLINE_LINE")
    if [[ -n "$suggestion" && "$suggestion" != "$READLINE_LINE" ]]; then
        READLINE_LINE="$suggestion"
        READLINE_POINT=${#READLINE_LINE}
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

if [[ -z "$PROMPT_COMMAND" ]]; then
    PROMPT_COMMAND="__shellsense_show_suggestion"
else
    PROMPT_COMMAND="__shellsense_show_suggestion;$PROMPT_COMMAND"
fi

trap '__shellsense_preexec "$BASH_COMMAND"' DEBUG
bind '\\C-e': __shellsense_accept_suggestion
bind '\\C-f': __shellsense_accept_suggestion
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

preexec_functions+=(__shellsense_preexec)
precmd_functions+=(__shellsense_precmd_suggest)
zle -N __shellsense_accept_suggestion
bindkey '^E' __shellsense_accept_suggestion
bindkey '^F' __shellsense_accept_suggestion
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
        python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    if d.get('success') and d.get('prediction'):
        print(d['prediction'])
except:
    pass
" (echo "$response" | read -l) 2>/dev/null
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

bind \\ce __shellsense_accept_suggestion
bind \\cf __shellsense_accept_suggestion
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
