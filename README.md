# GPS Denied Navigation

## Preprocessing
Upload a tiff to data and adjust the raster file path.
To create preprocessed DB, run:
```bash
python3 -m src.preprocessing.preprocess
```

## Converting to ONNX
Run:
```bash
python3 ./scripts/export_model_onnx.py
```
If you want your own model or config, load it.


## Testing ROS2 Locally
We will be using ROS2 Lyrical.

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

6. Build `px4_msgs` package. More can be found [here](https://github.com/PX4/px4_msgs):
```bash
chmod +x scripts/setup_px4_msgs.sh
./scripts/setup_px4_msgs.sh
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

#### SSH into the Pi:
```bash
ssh drone@<IP-address>
```

#### Cloning:
```bash
git clone --filter=blob:none --no-checkout \
  https://github.com/wynnson/GPS-Denied-Navigation.git

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

#### ROS2 and RPI Installation on Raspberry Pi:
This will also download other needed dependencies for the raspberry pi.
```bash
chmod +x scripts/install_rpi_deps.sh
./scripts/install_rpi_deps.sh
```

#### Setup PX4 ROS2 Package
`px4_msgs` is used to bridge ROS with Pixhawk. More about it can be found [here](https://github.com/PX4/px4_msgs). On the Raspberry Pi it will take a long time (30+ mins).

```bash
chmod +x scripts/setup_px4_msgs.sh
./scripts/setup_px4_msgs.sh
```

#### Download Micro XRCE DDS Middleware
This integrates PX4 and ROS2. See [here](https://docs.px4.io/main/en/middleware/uxrce_dds).

```bash
chmod +x scripts/install_micro_xrce_dds_agent.sh
./scripts/install_micro_xrce_dds_agent.sh
```

Running the agent:
```bash
MicroXRCEAgent serial --dev /dev/ttyAMA0 -b 921600
```
This will create a LOT of topics that you can subscribe to. See them via:
```bash
ros2 topic list
ros2 topic echo <topic>       # echo a certain topic 
```

#### Download Python Dependencies to Virtual Environment
```bash
uv sync --no-dev
```

#### Testing Raspberry Pi with uXRCE-DDS
1. Configure PX4 in QGroundControl (Skip to 3 if done):

```text
MAV_1_CONFIG = Disabled
UXRCE_DDS_CFG = TELEM2
SER_TEL2_BAUD = 921600
```

2. Reboot pixhawk
3. Start the Micro XRCE-DDS Agent on the Raspberry Pi. Check the Troubleshooting Raspberry Pi section for finding serial device.
```bash
micro-xrce-dds-agent serial --dev /dev/<serial-device> -b 921600
micro-xrce-dds-agent serial --dev /dev/ttyAMA0 -b 921600    # we use ttyAMA0 UART
```

#### Virtual Environment Setup
```
uv venv --system-site-packages            # IMPORTANT! to system ROS packages
uv sync --no-dev                          # install needed python deps
source .venv/bin/activate                 # activate venv
```

#### Running Ros Nodes:
```bash
python3 -m src.ros.visual_localization_node   # Localization node

```

### Troubleshooting Raspberry Pi Issues

#### Configuring WiFi:
```bash
sudo nano /etc/netplan/50-cloud-init.yaml   # Edit WiFi YAML config
sudo systemctl restart systemd-networkd     # Restart network service
sudo netplan generate                       # Parse config
sudo netplan apply                          # Try to connect
ip addr show wlan0                          # Check IP connection
```

#### No Telemetry?:
1. Use QGroundControl and connect Pixhawk directly with a microusb. 
2. Check `Vechile Configuration > Parameters` and search for `UXRCE_DDS_CFG`. It should be `Telem2`. 
3. Make sure nothing else is going through `Telem2`.
4. Check `MAV_1_CONFIG` and make sure it is `disabled`.


#### Startup Errors - Finding and Switching UART Devices:
1. Run `ls -l /dev/ttyAMA* /dev/ttyS* 2>/dev/null`
2. Make sure under `[all]`:
    ```
    enable_uart=1           # uart on
    dtoverlay=disable-bt    # bluetooth off
    ```
3. Remove old binding:

    Open up the txt file:
    ```bash
    sudo systemctl disable --now serial-getty@ttyAMA0.service
    sudo nano /boot/firmware/current/cmdline.txt
    ```
    You should see:
    ```text
    console=serial0,115200 multipath=off dwc_otg.lpm_enable=0 console=tty1 root=LABEL=writable rootfstype=ext4 panic=10 rootwait fixrtc
    ```
    Replace:
    ```
    console=serial0,115200
    ```
    With:
    ```
    console=ttyS0,115200
    ```
    We need to do this so our console doesn't trigger `SysRq` events. Leave: 
    ```
    console=tty1
    ```
    This prevents the Pixhawk and the Linux serial console from trying to use the same UART. We effectively did a switcheroo: ttyAMA0 is now reserved for the Pixhawk, while the Linux serial console is moved to a different UART.

4. Restart:
    ```bash
    sudo reboot
    ```

5. Check: `ls -l /dev/ttyAMA* /dev/ttyS* 2>/dev/null`. You should see `/dev/ttyAMA*`.


#### Can't find the baud rate?:
  - You can change it in QGroundControl under `Vehicle Configuration > Parameters`.
  - Make sure the Pixhawk and Raspberry Pi are configured to use the same baud rate.
  - Typical defaults:
    - **TELEM 1:** `57600`
    - **TELEM 2:** `921600`