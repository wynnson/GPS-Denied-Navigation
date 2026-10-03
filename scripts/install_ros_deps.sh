#!/usr/bin/env bash

# NOTE:
# Need perms: chmod +x scripts/install_ros_deps.sh
# Run: sudo ./scripts/install_ros_deps.sh

set -e

apt update

apt install -y \
  curl \
  software-properties-common

add-apt-repository -y universe

curl -sSL \
  https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu resolute main" \
  > /etc/apt/sources.list.d/ros2.list

apt update

apt install -y \
  ros-lyrical-ros-base \
  ros-lyrical-cv-bridge \
  ros-lyrical-sensor-msgs \
  ros-lyrical-geometry-msgs \
  python3-pip \
  python3-opencv \
  python3.14-venv \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool

curl -LsSf https://astral.sh/uv/install.sh | sh

rm -rf /var/lib/apt/lists/*