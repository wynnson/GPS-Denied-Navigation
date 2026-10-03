# GPS Denied Navigation

## Testing ROS2 Locally

### Docker Setup
1.  Build Docker container (skip to step 2 if exists):
```bash
docker run -dit \
  --name uav-ros \
  -v "$(pwd)":/workspace/app \
  -w /workspace/app \
  ros:latest \
  bash
```
This:
- creates a container named uav-ros
- mounts the current repository into /workspace/app
- uses /workspace/app as the working directory
- keeps the container running in the background

2. If the container already exists but is stopped:
```bash
docker start uav-ros
```

3. Open a shell inside the container:
```bash
docker exec -it uav-ros bash
```

4. Install deps:
```bash
cd /workspace/app
bash scripts/install_ros_deps.sh
export PATH="/root/.local/bin:$PATH"      # save uv to path
```

5. Virtual Environment:
```
uv venv --system-site-packages            # allow access to system ROS packages
uv sync --no-dev                          # install needed python deps
source .venv/bin/activate                 # activate venv
```

6. Build `px4_msg` package:
```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/PX4/px4_msgs.git
cd ~/ros2_ws
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --packages-select px4_msgs
source ~/ros2_ws/install/setup.bash
ros2 interface show px4_msgs/msg/AuxGlobalPosition    # verify packcage works
```

7. Open another terminal and run visual localization node:
```bash
docker exec -it uav-ros bash
```
Inside:
```bash
cd /workspace/app

source .venv/bin/activate
source /opt/ros/$ROS_DISTRO/setup.bash
source ~/ros2_ws/install/setup.bash

python3 -m src.ros.visual_localization_node   # gets estimates of local
```
This subscribes to `/camera/image` and publishes estimates to `/fmu/in/aux_global_position`

8. Open another terminal and run test node (mocks camera):
```bash
docker exec -it uav-ros bash
```
Inside:
```bash
cd /workspace/app

source .venv/bin/activate
source /opt/ros/$ROS_DISTRO/setup.bash
source ~/ros2_ws/install/setup.bash

python3 src/ros/tests/visual_localization_test.py # publishes image (mocks camera)
```
This publishes image to `/camera/image`. The localization node should receive the image, run inference, estimate a position, and publish the result.

9. Open another terminal and inspect published PX4 mesage:
```bash
docker exec -it uav-ros bash
source /opt/ros/$ROS_DISTRO/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 topic echo /fmu/in/aux_global_position
```


#### Example outputs:
```text
# Localization node
[ predict ] finished in 0.61 seconds
[INFO] [1791047577.615547170] [visual_localization_node]: Est Lon: -84.40464278874128, Est Lat: 33.77676050536601, Est Error: 29.50274685137785

# Test node
[INFO] [1791047571.981919667] [test_visual_localization_node]: Published test image

# PX4 message
---
timestamp: 1791046984563373
timestamp_sample: 1791046983986775
id: 0
source: 2
lat: 33.77676050536601
lon: -84.40464278874128
alt: 0.0
eph: 29.50274658203125
epv: 0.0
lat_lon_reset_counter: 0
---
```



## Raspberry Pi (4B)

#### Configuring WiFi:
```bash
sudo nano /etc/netplan/50-cloud-init.yaml   # Edit WiFi YAML config
sudo systemctl restart systemd-networkd     # Restart network service
sudo netplan generate                       # Parse config
sudo netplan apply                          # Try to connect
ip addr show wlan0                          # Check IP connection
```

#### SSH into the Pi:
```bash
ssh drone@<IP-address>
```

#### Cloning:
```bash
git clone --filter=blob:none --no-checkout https://github.com/wynnson/GPS-Denied-Navigation.git
cd GPS-Denied-Navigation

# Only pull needed files (ignore using !/)
git sparse-checkout init --no-cone
git sparse-checkout set --stdin <<'EOF'
/*
!/notebooks/
!/visualization/
!/data/GT_NW.tif
EOF

git checkout
```

#### ROS2 on Raspberry Pi:
```bash
chmod +x scripts/install_rpi_deps.sh    # If missing permision
./scripts/install_rpi_deps.sh           # Installs needed deps and uv
```

#### Download Python Dependencies to Virtual Environment
```bash
uv sync --no-default-groups --group pi
```

#### Testing Pixhawk to Raspberry Pi

```bash
# Note Telem2 baudrate is 921600
mavproxy.py --master=/dev/serial0 --baudrate 921600

# Useful commands after running the above:
watch HIGHRES_IMU                      # Accel, gyro, mag, pressure
watch ATTITUDE                         # Roll, pitch, yaw
watch ATTITUDE_QUATERNION              # Quaternion [w, x, y, z]
watch ODOMETRY                         # EKF pose, velocity, covariance
watch LOCAL_POSITION_NED               # Local NED position + velocity
watch GLOBAL_POSITION_INT              # Fused lat, lon, alt, heading
watch GPS_RAW_INT                      # Raw GPS fix, sats, accuracy
watch ESTIMATOR_STATUS                 # EKF innovation ratios / health
watch VFR_HUD                          # Airspeed, groundspeed, heading, alt
watch BATTERY_STATUS                   # Voltage, current, battery state
watch SYS_STATUS                       # Overall system health
watch HEARTBEAT                        # MAVLink connection / vehicle state
watch VIBRATION                        # IMU vibration and clipping
watch SCALED_PRESSURE                  # Barometer pressure
watch ALTITUDE                         # Various altitude estimates
watch EXTENDED_SYS_STATE               # Landed / VTOL state
```

#### Troubleshooting Raspberry Pi Issues

<!-- - **Not receiving telemetry from the Pixhawk?**
    1. Check the wiring between the Raspberry Pi and Pixhawk.
    2. Connect the Pixhawk to **QGroundControl**.
    3. Go to **Vehicle Setup → Parameters**.
    4. Search for `MAV_1_CONFIG`.
    5. Check whether `MAV_1_CONFIG` is disabled.
    6. If disabled, switch it to **TELEM 2**. -->

- **Can't find the baud rate?**
  - You can change it in **QGroundControl** under **Vehicle Setup → Parameters**.
  - Make sure the Pixhawk and Raspberry Pi are configured to use the same baud rate.
  - Typical defaults:
    - **TELEM 1:** `57600`
    - **TELEM 2:** `921600`