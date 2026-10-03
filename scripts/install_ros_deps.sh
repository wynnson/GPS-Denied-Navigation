#!/usr/bin/env bash

# NOTE: If running into perms issues use:
# chmod +x scripts/install_ros_deps.sh

set -e

apt update

apt install -y \
    python3-pip \
    python3-opencv \
    python3.14-venv \
    ros-$ROS_DISTRO-cv-bridge \
    ros-$ROS_DISTRO-sensor-msgs \
    ros-$ROS_DISTRO-geometry-msgs

curl -LsSf https://astral.sh/uv/install.sh | sh

rm -rf /var/lib/apt/lists/*