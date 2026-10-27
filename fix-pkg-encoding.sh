#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
target_file="$project_dir/.venv/lib/python3.14/site-packages/nodriver/cdp/network.py"
line="$(LC_ALL=C sed -n '1345p' "$target_file")"

if [[ "$line" =~ ^[[:space:]]*\# ]]; then
    sed -i '1345d' "$target_file"
    printf '%s\n' 'Deleted comment on line 1345.'
else
    printf '%s\n' 'Line 1345 is not a comment; nothing changed.'
fi
