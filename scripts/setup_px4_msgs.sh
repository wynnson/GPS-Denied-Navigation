#!/usr/bin/env bash

set -e

source /opt/ros/lyrical/setup.bash

mkdir -p "$HOME/ros2_ws/src"

PX4_MSGS_BRANCH="release/1.17"    # change version if needed
PX4_MSGS_DIR="$HOME/ros2_ws/src/px4_msgs"

if [ ! -d "$PX4_MSGS_DIR" ]; then
  git clone \
    --branch "$PX4_MSGS_BRANCH" \
    --single-branch \
    https://github.com/PX4/px4_msgs.git \
    "$PX4_MSGS_DIR"
fi

cd "$HOME/ros2_ws"

colcon build --packages-select px4_msgs

source "$HOME/ros2_ws/install/setup.bash"


# Add ROS 2 and px4_msgs setup scripts to ~/.bashrc so every new shell is ROS-ready
if ! grep -q 'source /opt/ros/lyrical/setup.bash' "$HOME/.bashrc"; then
  echo 'source /opt/ros/lyrical/setup.bash' >> "$HOME/.bashrc"
fi

if ! grep -q 'source ~/ros2_ws/install/setup.bash' "$HOME/.bashrc"; then
  echo 'source ~/ros2_ws/install/setup.bash' >> "$HOME/.bashrc"
fi


echo "px4_msgs setup complete"