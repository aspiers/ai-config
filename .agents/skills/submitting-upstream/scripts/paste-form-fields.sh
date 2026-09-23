#!/usr/bin/env bash
# Load form-field files onto the clipboard one at a time, announcing each with
# a desktop notification that names the field to paste into, and advance on a
# timer so the user never has to report back between pastes.
#
# Usage: paste-form-fields.sh [-f FIRST_DELAY] [-d DELAY] [-t DISPLAY_SECS] FILE...
#
# The field label comes from the filename: 2-problem-or-use-case.txt becomes
# "Problem or use case". A first line of "#NOTE: text" is shown in the
# notification and not copied.
set -euo pipefail

first_delay=5
delay=5
display_secs=10

usage() {
    echo "usage: ${0##*/} [-f FIRST_DELAY] [-d DELAY] [-t DISPLAY_SECS] FILE..." >&2
    exit 2
}

while getopts 'f:d:t:h' opt; do
    case $opt in
        f) first_delay=$OPTARG ;;
        d) delay=$OPTARG ;;
        t) display_secs=$OPTARG ;;
        *) usage ;;
    esac
done
shift $((OPTIND - 1))
(($# > 0)) || usage

if [[ -n ${WAYLAND_DISPLAY:-} ]] && command -v wl-copy >/dev/null; then
    clip_in() { wl-copy; }
    clip_out() { wl-paste -n; }
elif [[ -n ${DISPLAY:-} ]] && command -v xclip >/dev/null; then
    clip_in() { xclip -selection clipboard; }
    clip_out() { xclip -selection clipboard -o; }
elif [[ -n ${DISPLAY:-} ]] && command -v xsel >/dev/null; then
    clip_in() { xsel --clipboard --input; }
    clip_out() { xsel --clipboard --output; }
elif command -v pbcopy >/dev/null; then
    clip_in() { pbcopy; }
    clip_out() { pbpaste; }
else
    echo "no clipboard tool found (wl-copy, xclip, xsel or pbcopy)" >&2
    exit 1
fi

if command -v notify-send >/dev/null; then
    notify() { notify-send -t $((display_secs * 1000)) "$1" "$2"; }
elif command -v osascript >/dev/null; then
    # Why: macOS decides how long a notification stays up; -t cannot apply.
    notify() {
        osascript - "$1" "$2" <<'EOF'
on run argv
    display notification (item 2 of argv) with title (item 1 of argv)
end run
EOF
    }
else
    echo "warning: no notification tool; announcing in this terminal only" >&2
    notify() { :; }
fi

field_label() {
    local name
    name=$(basename "$1" .txt)
    name=${name#*-}
    name=${name//-/ }
    # Why not ${name^}: macOS still ships bash 3.2.
    printf '%s%s' "$(printf '%s' "${name:0:1}" | tr '[:lower:]' '[:upper:]')" "${name:1}"
}

total=$#
i=0
for file in "$@"; do
    i=$((i + 1))
    label=$(field_label "$file")
    note=''
    content=$(cat "$file")
    if [[ $content == '#NOTE: '* ]]; then
        note=${content%%$'\n'*}
        note=${note#'#NOTE: '}
        content=${content#*$'\n'}
    fi

    # Why printf '%s': a trailing newline lands in the form as a stray blank line.
    printf '%s' "$content" | clip_in
    # Why: a silent copy failure would mean pasting stale text into a public tracker.
    if [[ $(clip_out) != "$content" ]]; then
        notify "Paste aborted" "Clipboard check failed for $label"
        echo "clipboard mismatch for $file" >&2
        exit 1
    fi

    body="Paste into: $label"
    [[ -n $note ]] && body+=" — $note"
    echo "$(date +%T) [$i/$total] $label"

    if ((i == total)); then
        notify "Field $i/$total ready (last)" "$body"
        break
    fi
    wait_s=$delay
    ((i == 1)) && wait_s=$first_delay
    notify "Field $i/$total ready, next in ${wait_s}s" "$body"
    sleep "$wait_s"
done
