#!/usr/bin/env bash

set -eo pipefail

REPO="$HOME/GPS-Denied-Navigation"

echo "[START] GPS-Denied Navigation Stack"

source /opt/ros/lyrical/setup.bash              # ROS 2
source "$HOME/ros2_ws/install/setup.bash"       # PX4 messages
source "$REPO/.venv/bin/activate"               # Project environment

cd "$REPO"

cleanup() {
    echo
    echo "[STOP] Shutting down stack..."

    kill "${CAMERA_PID:-}" 2>/dev/null || true
    kill "${LOCALIZER_PID:-}" 2>/dev/null || true
    kill "${XRCE_PID:-}" 2>/dev/null || true

    wait 2>/dev/null || true

    echo "[STOP] Stack stopped."
}

trap cleanup EXIT SIGINT SIGTERM

echo "Beginning startup..."
sleep 2         # Buffer

# ============= START AGENT ============= #
echo "[START] Micro XRCE-DDS Agent"
MicroXRCEAgent serial \
    --dev /dev/ttyAMA0 \
    -b 921600 &
XRCE_PID=$!     # stores process ID
sleep 15        # Adjust as need be (sec from power to launch)


# ============= START LOCALIZATION ============= #
echo "[START] Visual Localization"
python3 -m src.ros.visual_localization_node &
LOCALIZER_PID=$!
sleep 2


# ============= START CAMERA ============= #
echo "[START] Camera Node"
python3 -m src.ros.camera_node &
CAMERA_PID=$!


echo "[READY] All processes started"
echo "XRCE PID:      $XRCE_PID"
echo "Localizer PID: $LOCALIZER_PID"
echo "Camera PID:    $CAMERA_PID"


# If any one process dies, stop the whole stack.
wait -n "$XRCE_PID" "$LOCALIZER_PID" "$CAMERA_PID" || true

echo "[ERROR] One process exited."
exit 1