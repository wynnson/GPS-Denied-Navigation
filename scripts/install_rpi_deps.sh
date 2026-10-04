#!/usr/bin/env bash

# NOTE:
# Need perms:
#   chmod +x scripts/install_rpi_deps.sh
#
# Run:
#   ./scripts/install_rpi_deps.sh

set -e

# ===== Ubuntu / ROS setup =====

sudo apt update

sudo apt install -y \
  curl \
  software-properties-common

sudo add-apt-repository -y universe

sudo curl -sSL \
  https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu resolute main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update

sudo apt install -y \
  ros-lyrical-ros-base \
  ros-lyrical-cv-bridge \
  ros-lyrical-sensor-msgs \
  ros-lyrical-geometry-msgs \
  python3-pip \
  python3-opencv \
  python3.14-venv \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  rpicam-apps

# ===== uv installation =====

curl -LsSf https://astral.sh/uv/install.sh | sh

export PATH="$HOME/.local/bin:$PATH"

if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc"; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

# ===== cleanup =====

sudo rm -rf /var/lib/apt/lists/*