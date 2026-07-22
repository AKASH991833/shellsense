from __future__ import annotations


def _get_bash_hooks() -> str:
    return """# ShellSense AI - Shell Hooks
__shellsense_history_learn() {
    local cmd="$1"
    if [[ -n "$cmd" && -S /tmp/shellsense-daemon.sock ]]; then
        local request=$(printf '{"type":"learn","command":"%%s"}' "$cmd")
        echo "$request" | nc -U /tmp/shellsense-daemon.sock 2>/dev/null &
    fi
}

__shellsense_preexec() {
    local cmd="$1"
    local warnings
    warnings=$(ss check-command "$cmd" 2>/dev/null)
    if [[ -n "$warnings" ]]; then
        echo "[ShellSense] Warning: $warnings" >&2
    fi
    __shellsense_history_learn "$cmd" &
}

__shellsense_inline_suggest() {
    local partial="${READLINE_LINE:0:READLINE_POINT}"
    if [[ -z "$partial" || ! -S /tmp/shellsense-daemon.sock ]]; then
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
except: pass
s.close()
" 2>/dev/null)
    fi
    if [[ -n "$response" ]]; then
        local prediction=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prediction',''))" 2>/dev/null)
        if [[ -n "$prediction" && "$prediction" != "$partial" ]]; then
            local rest="${prediction#$partial}"
            if [[ -n "$rest" ]]; then
                echo -ne "\\033[90m${rest}\\033[0m"
            fi
        fi
    fi
}

__shellsense_accept_suggest() {
    if [[ -z "$READLINE_LINE" || ! -S /tmp/shellsense-daemon.sock ]]; then
        return
    fi
    local request=$(printf '{"type":"suggest","partial":"%%s","limit":1}' "$READLINE_LINE")
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
except: pass
s.close()
" 2>/dev/null)
    fi
    if [[ -n "$response" ]]; then
        local prediction=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prediction',''))" 2>/dev/null)
        if [[ -n "$prediction" && "$prediction" != "$READLINE_LINE" ]]; then
            local rest="${prediction#$READLINE_LINE}"
            READLINE_LINE="$prediction"
            READLINE_POINT=${#READLINE_LINE}
        fi
    fi
}

if [[ -z "$PROMPT_COMMAND" ]]; then
    PROMPT_COMMAND="__shellsense_inline_suggest"
else
    PROMPT_COMMAND="__shellsense_inline_suggest;$PROMPT_COMMAND"
fi

trap '__shellsense_preexec "$BASH_COMMAND"' DEBUG
bind -x '"\\C-e": __shellsense_accept_suggest'
bind -x '"\\C-f": __shellsense_accept_suggest'
"""


def _get_zsh_hooks() -> str:
    return """# ShellSense AI - Shell Hooks
__shellsense_preexec() {
    local cmd="$1"
    local warnings
    warnings=$(ss check-command "$cmd" 2>/dev/null)
    if [[ -n "$warnings" ]]; then
        echo "[ShellSense] Warning: $warnings" >&2
    fi
}

__shellsense_precmd() {
    local last_cmd=$(fc -ln -1 2>/dev/null | sed 's/^[[:space:]]*//')
    if [[ -n "$last_cmd" && -S /tmp/shellsense-daemon.sock ]]; then
        local request=$(printf '{"type":"suggest","partial":"%%s","limit":1}' "$last_cmd")
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
except: pass
s.close()
" 2>/dev/null)
        fi
        if [[ -n "$response" ]]; then
            local prediction=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prediction',''))" 2>/dev/null)
            if [[ -n "$prediction" && "$prediction" != "$last_cmd" ]]; then
                local rest="${prediction#$last_cmd}"
                if [[ -n "$rest" ]]; then
                    print -Pn "%%F{242}${rest}%%f"
                fi
            fi
        fi
    fi
}

autoload -Uz add-zsh-hook
add-zsh-hook preexec __shellsense_preexec
add-zsh-hook precmd __shellsense_precmd

# Auto-suggest widget
__shellsense_suggest_widget() {
    local partial="$BUFFER"
    if [[ -z "$partial" || ! -S /tmp/shellsense-daemon.sock ]]; then
        POSTDISPLAY=""
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
except: pass
s.close()
" 2>/dev/null)
    fi
    if [[ -n "$response" ]]; then
        local prediction=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prediction',''))" 2>/dev/null)
        if [[ -n "$prediction" && "$prediction" != "$partial" ]]; then
            local rest="${prediction#$partial}"
            POSTDISPLAY="$rest"
        else
            POSTDISPLAY=""
        fi
    fi
}

__shellsense_accept_suggestion() {
    if [[ -n "$POSTDISPLAY" ]]; then
        BUFFER="$BUFFER$POSTDISPLAY"
        CURSOR=${#BUFFER}
        POSTDISPLAY=""
    fi
}

zle -N __shellsense_suggest_widget
zle -N __shellsense_accept_suggestion
bindkey '^E' __shellsense_accept_suggestion
bindkey '^F' __shellsense_accept_suggestion

# Integrate with zsh-autosuggestions if available
if typeset -f _zsh_autosuggest_strategy_match &>/dev/null; then
    ZSH_AUTOSUGGEST_STRATEGY=match
fi
"""


def _get_fish_hooks() -> str:
    return """# ShellSense AI - Shell Hooks
function __shellsense_preexec --on-event fish_preexec
    set -l cmd $argv[1]
    set -l warnings (ss check-command "$cmd" 2>/dev/null)
    if test -n "$warnings"
        echo "[ShellSense] Warning: $warnings" >&2
    end
end

function __shellsense_precmd --on-event fish_prompt
    set -l last_cmd (history search --reverse --max=1 2>/dev/null | head -1)
    if test -n "$last_cmd" -a -S /tmp/shellsense-daemon.sock
        set -l request (printf '{"type":"suggest","partial":"%%s","limit":1}' "$last_cmd")
        set -l response (echo $request | nc -U /tmp/shellsense-daemon.sock 2>/dev/null)
        if test -z "$response"
            set response (python3 -c "
import socket, json
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect('/tmp/shellsense-daemon.sock')
    s.sendall(b'$request')
    data = s.recv(65536)
    print(data.decode())
except: pass
s.close()
" 2>/dev/null)
        end
        if test -n "$response"
            set -l prediction (echo $response | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prediction',''))" 2>/dev/null)
            if test -n "$prediction" -a "$prediction" != "$last_cmd"
                set -l rest (string replace "$last_cmd" "" "$prediction")
                if test -n "$rest"
                    echo -ns (set_color brblack) "$rest" (set_color normal)
                end
            end
        end
    end
end

function fish_autosuggestion
    set -l cmd (commandline -op | head -1)
    if test -z "$cmd"
        return
    end
    if not test -S /tmp/shellsense-daemon.sock
        return
    end
    set -l request (printf '{"type":"suggest","partial":"%%s","limit":1}' "$cmd")
    set -l response (echo $request | nc -U /tmp/shellsense-daemon.sock 2>/dev/null)
    if test -z "$response"
        set response (python3 -c "
import socket, json
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect('/tmp/shellsense-daemon.sock')
    s.sendall(b'$request')
    data = s.recv(65536)
    print(data.decode())
except: pass
s.close()
" 2>/dev/null)
    end
    if test -n "$response"
        set -l prediction (echo $response | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prediction',''))" 2>/dev/null)
        if test -n "$prediction" -a "$prediction" != "$cmd"
            set -l rest (string replace "$cmd" "" "$prediction")
            if test -n "$rest"
                echo -ns (set_color brblack) "$rest" (set_color normal)
            end
        end
    end
end

bind \\ce accept-autosuggestion
bind \\cf accept-autosuggestion
"""


def get_hook_script(shell: str) -> str:
    generators = {
        "bash": _get_bash_hooks,
        "zsh": _get_zsh_hooks,
        "fish": _get_fish_hooks,
    }
    generator = generators.get(shell)
    if generator:
        return generator()
    return ""


def get_prompt_snippet(shell: str) -> str:
    snippets = {
        "bash": """
# ShellSense AI - Prompt Integration
if [[ -z "$SS_NO_PROMPT" ]]; then
    PS1="\\[\\e[38;5;45m\\]ss\\[\\e[0m\\] $PS1"
fi
""",
        "zsh": """
# ShellSense AI - Prompt Integration
if [[ -z "$SS_NO_PROMPT" ]]; then
    PROMPT="%F{45}ss%f $PROMPT"
fi
""",
        "fish": """
# ShellSense AI - Prompt Integration
if not set -q SS_NO_PROMPT
    set -g fish_prompt "ss $fish_prompt"
end
""",
    }
    return snippets.get(shell, "")
