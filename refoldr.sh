#!/bin/bash
# refoldr.sh - create venv, install dependencies, run ReFoldr.py


# get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# run everything in a subshell to isolate venv activation
(
    # create venv if it doesn't exist
    if [ ! -d "$SCRIPT_DIR/.venv" ]; then
        python3 -m venv "$SCRIPT_DIR/.venv"
        #"$SCRIPT_DIR/.venv/bin/python" -m pip install --upgrade pip
        "$SCRIPT_DIR/.venv/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"
    fi

    # activate venv
    source "$SCRIPT_DIR/.venv/bin/activate"

    # run the script with all arguments, from the current folder (Music)
    "$SCRIPT_DIR/ReFoldr.py" "$@"

    # deactivate venv automatically
    deactivate 2>/dev/null
)