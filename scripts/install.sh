#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "$0")"

chmod +x "$SCRIPT_DIR/install_px4_msgs.sh"
chmod +x "$SCRIPT_DIR/install_rpi_deps.sh"
chmod +x "$SCRIPT_DIR/install_micro_xrce_dds_agent.sh"

bash "$SCRIPT_DIR/install_px4_msgs.sh"
bash "$SCRIPT_DIR/install_rpi_deps.sh"
source "$HOME/.local/bin/env"
bash "$SCRIPT_DIR/install_micro_xrce_dds_agent.sh"

cd "$HOME/GPS-Denied-Navigation"
uv venv --system-site-packages
uv sync --no-dev
source .venv/bin/activate

echo "Installation complete!"
