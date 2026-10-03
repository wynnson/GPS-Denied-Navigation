#!/usr/bin/env bash

set -e

source /opt/ros/lyrical/setup.bash

mkdir -p "$HOME/ros2_ws/src"

if [ ! -d "$HOME/ros2_ws/src/px4_msgs" ]; then
  git clone https://github.com/PX4/px4_msgs.git \
    "$HOME/ros2_ws/src/px4_msgs"
fi

cd "$HOME/ros2_ws"

colcon build --packages-select px4_msgs

source "$HOME/ros2_ws/install/setup.bash"

echo "px4_msgs setup complete"