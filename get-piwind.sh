#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GIT_PIWIND=OasisPiWind

if [ ! -d "$SCRIPT_DIR/$GIT_PIWIND/.git" ]; then
    echo "--- Cloning PiWind model ---"
    mkdir -p "$SCRIPT_DIR/$GIT_PIWIND"
    cd "$SCRIPT_DIR/$GIT_PIWIND"
    git clone --depth 1 --branch "${VERS_PIWIND}" "https://github.com/OasisLMF/$GIT_PIWIND.git" .
    cd "$SCRIPT_DIR"
    echo ""
else
    echo "  -> PiWind model already cloned"
    echo ""
fi
