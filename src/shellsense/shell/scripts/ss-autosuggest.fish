# ShellSense AI - Fish Auto-Suggestions
# Source this in your config.fish: source ~/.shellsense/ss-autosuggest.fish

set -g __shellsense_daemon_socket /tmp/shellsense-daemon.sock

function __shellsense_get_suggestion -a partial
    if test -z "$partial"
        echo ""
        return
    end
    if not test -S "$__shellsense_daemon_socket"
        echo ""
        return
    end
    set -l request (printf '{"type":"suggest","partial":"%s","limit":1}' "$partial")
    set -l response (echo $request | nc -U "$__shellsense_daemon_socket" 2>/dev/null)
    if test -z "$response"
        set response (python3 -c "
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
    end
    if test -n "$response"
        set -l prediction (echo $response | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prediction',''))" 2>/dev/null)
        echo $prediction
    end
end

# Fish has built-in autosuggestions via fish_autosuggestion function
function fish_autosuggestion
    set -l cmd (commandline -op | head -1)
    if test -z "$cmd"
        return
    end
    set -l suggestion (__shellsense_get_suggestion "$cmd")
    if test -n "$suggestion" -a "$suggestion" != "$cmd"
        set -l rest (string replace "$cmd" "" "$suggestion")
        if test -n "$rest"
            echo -ns (set_color brblack) "$rest" (set_color normal)
        end
    end
end

# Accept suggestion with Ctrl-E or Right
function __shellsense_accept_suggestion --on-event fish_prompt
    # Fish handles autosuggestions natively
end

# Key bindings
bind \ce accept-autosuggestion
bind \cf accept-autosuggestion

# Tab completion
if type -q shellsense
    shellsense show-completion fish 2>/dev/null | source
end
