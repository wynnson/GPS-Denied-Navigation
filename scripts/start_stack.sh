#!/usr/bin/env bash
set -euo pipefail

REPO="$HOME/GPS-Denied-Navigation"

echo "[START] GPS-Denied Navigation Stack"

# ROS 2
source /opt/ros/lyrical/setup.bash

# PX4 messages
source "$HOME/ros2_ws/install/setup.bash"

# Project environment
source "$REPO/.venv/bin/activate"

cd "$REPO"

cleanup() {
    echo
    echo "[STOP] Shutting down stack..."

    kill "${TEST_PID:-}" 2>/dev/null || true
    kill "${LOCALIZER_PID:-}" 2>/dev/null || true
    kill "${XRCE_PID:-}" 2>/dev/null || true

    wait 2>/dev/null || true

    echo "[STOP] Stack stopped."
}

trap cleanup EXIT SIGINT SIGTERM


# ============= START AGENT ============= #
echo "[START] Micro XRCE-DDS Agent"
MicroXRCEAgent serial \
    --dev /dev/ttyAMA0 \
    -b 921600 &
XRCE_PID=$! # stores process ID
sleep 3


# ============= START LOCALIZATION ============= #
echo "[START] Visual Localization"
python3 -m src.ros.visual_localization_node &
LOCALIZER_PID=$!
sleep 2


# ============= START CAMERA ============= #
echo "[START] Test Camera Node"
python3 -m src.ros.visual_localization_test --pi &
TEST_PID=$!


echo "[READY] All processes started"
echo "XRCE PID:      $XRCE_PID"
echo "Localizer PID: $LOCALIZER_PID"
echo "Test PID:      $TEST_PID"


# If any one process dies, stop the whole stack.
wait -n "$XRCE_PID" "$LOCALIZER_PID" "$TEST_PID"

echo "[ERROR] One process exited."
exit 1