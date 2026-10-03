#!/usr/bin/env bash

set -e

# Remove Snap version if installed
if snap list micro-xrce-dds-agent >/dev/null 2>&1; then
  sudo snap remove micro-xrce-dds-agent
fi

# Install build dependencies
sudo apt update
sudo apt install -y \
  git \
  cmake \
  build-essential

# Clone DDS v2 Agent used with stock PX4 firmware
cd "$HOME"

if [ ! -d "$HOME/Micro-XRCE-DDS-Agent" ]; then
  git clone -b v2.4.3 \
    https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
fi

cd "$HOME/Micro-XRCE-DDS-Agent"

# Build and install
mkdir -p build
cd build

cmake ..
make -j2

sudo make install
sudo ldconfig /usr/local/lib/

echo
echo "Micro XRCE-DDS Agent installed successfully."
echo "Verify with:"
echo "  MicroXRCEAgent --help"
echo
echo "Run on Raspberry Pi UART with:"
echo "  MicroXRCEAgent serial --dev /dev/ttyAMA0 -b 921600"