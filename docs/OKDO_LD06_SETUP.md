# OKDO Lidar HAT (LD06) Setup Guide

## Hardware Overview

The OKDO Lidar HAT mounts directly on the Raspberry Pi 40-pin GPIO header using UART communication.

## Pin Connections

### OKDO LD06 HAT (Sits on top of Pi GPIO):
```
Raspberry Pi 40-Pin Header
┌─────────────────────────────┐
│  Pin 1  (3.3V)              │
│  Pin 2  (5V)     ←──────────┼─── LD06 Power (5V)
│  Pin 3  (GPIO 2 SDA) ←──────┼─── IMU SDA (I2C)
│  Pin 4  (5V)                │
│  Pin 5  (GPIO 3 SCL) ←──────┼─── IMU SCL (I2C)
│  Pin 6  (GND)       ←──────┼─── LD06 & IMU Ground
│  Pin 7  (GPIO 4)           │
│  Pin 8  (GPIO 14 TXD) ←─────┼─── LD06 RX (UART)
│  Pin 9  (GND)              │
│  Pin 10 (GPIO 15 RXD) ←─────┼─── LD06 TX (UART)
│  ...                       │
└─────────────────────────────┘
```

### Connection Summary:

**OKDO LD06 HAT:**
- Mounts on entire 40-pin GPIO header
- Uses GPIO 14/15 (UART) for communication
- Uses 5V and GND for power
- Motor and sensor built into the HAT

**IMU (MPU6050) - Connect to HAT pass-through pins:**
- **5V** → Pin 2 or 4 on HAT
- **GND** → Pin 6 on HAT
- **SDA** → Pin 3 (GPIO 2) on HAT
- **SCL** → Pin 5 (GPIO 3) on HAT

**No conflicts!** LD06 uses UART (GPIO 14/15), IMU uses I2C (GPIO 2/3)

## Software Setup

### Step 1: Enable UART on Raspberry Pi

**On the robot, edit `/boot/firmware/config.txt`:**

```bash
sudo nano /boot/firmware/config.txt
```

**Add/modify these lines:**
```ini
# Enable UART for LD06 Lidar
enable_uart=1
dtoverlay=disable-bt

# Make sure miniUART is not on GPIO 14/15
# (Bluetooth will be disabled)
```

**Disable the serial console:**
```bash
sudo raspi-config
# Navigate to: Interface Options → Serial Port
# "Would you like a login shell over serial?" → No
# "Would you like the serial hardware enabled?" → Yes
```

**Reboot:**
```bash
sudo reboot
```

**Verify UART is available:**
```bash
ls -l /dev/ttyAMA0
# Should show: crw-rw---- 1 root dialout
```

**Add user to dialout group:**
```bash
sudo usermod -a -G dialout $USER
# Logout and login again
```

### Step 2: Install LD06 ROS2 Driver

**On the robot:**
```bash
cd ~/dev_ws/src

# Clone the LD06 driver (linorobot version - well maintained)
git clone https://github.com/linorobot/ldlidar.git

# OR use the official driver:
# git clone https://github.com/ldrobotSensorTeam/ldlidar_stl_ros2.git

# Build
cd ~/dev_ws
colcon build --packages-select ldlidar_stl_ros2
source install/setup.bash

# If build fails, you may need dependencies:
# sudo apt-get update
# sudo apt-get install -y ros-humble-rclcpp ros-humble-sensor-msgs
```

### Step 3: Test the LD06

**Stop your normal launch and test the lidar:**
```bash
# On robot:
ros2 launch ros_bot lidar_ld06.launch.py
```

**On desktop, check the scan:**
```bash
ros2 topic hz /scan
# Should see ~10Hz

ros2 topic echo /scan --once
# Should see clean scan data with range 0.02m - 12m
```

### Step 4: Update Velocity Limits (Optional)

Now that you have 10Hz lidar (2x faster), you can move faster:

**In `config/my_controllers.yaml`:**
```yaml
# Can now safely double the velocities:
linear.x.max_velocity: 0.52  # Was 0.26
angular.z.max_velocity: 1.0  # Was 0.5
```

**In `config/nav2_params.yaml`:**
```yaml
max_vel_x: 0.52  # Was 0.26
max_vel_theta: 1.0  # Was 0.5
```

**In `config/joystick.yaml`:**
```yaml
scale_linear_turbo:
  x: 0.52  # Was 0.26
scale_angular_turbo:
  yaw: 1.0  # Was 0.5
```

### Step 5: Update Scan Cleaner Parameters

**In `launch/lidar_ld06.launch.py`** (already done):
```python
'min_range': 0.05,  # LD06 is much cleaner, can use tighter filter
'max_range': 12.0,  # LD06 max range
```

### Step 6: Deploy to Robot

**Copy updated config to robot:**
```bash
# From desktop:
scp -r ~/dev_ws/src/ros_bot burf2000@pi4-ros.local:~/dev_ws/src/

# SSH to robot:
ssh burf2000@pi4-ros.local
cd ~/dev_ws
colcon build --packages-select ros_bot
source install/setup.bash
```

## Running the System

### On Robot:
```bash
ros2 launch ros_bot launch_robot.launch.py
```

### On Desktop:
```bash
ros2 launch ros_bot desktop.launch.py rviz:=true
```

## Troubleshooting

### Lidar not found / Permission denied:
```bash
# Check device exists:
ls -l /dev/ttyAMA0

# Add to dialout group:
sudo usermod -a -G dialout $USER
# Then logout and login

# Check for conflicts:
sudo systemctl status serial-getty@ttyAMA0.service
# Should be disabled
```

### Scan direction reversed:
In `lidar_ld06.launch.py`, change:
```python
'laser_scan_dir': False,  # Flip scan direction
```

### Low scan rate:
```bash
# Check actual rate:
ros2 topic hz /scan

# Should be ~10Hz. If lower:
# 1. Check CPU usage on Pi
# 2. Verify UART baud rate is 230400 (parameter: port_baudrate, not serial_baudrate)
# 3. Check for interference
```

## Performance Comparison

| Metric | XV-11 (Old) | LD06 (New) | Improvement |
|--------|-------------|------------|-------------|
| Scan Rate | 5Hz | 10Hz | 2x faster |
| Noise | 30% | <5% | 6x cleaner |
| Min Range | 6cm | 2cm | 3x closer |
| Max Range | 5m | 12m | 2.4x longer |

## Expected Results

After switching to LD06:
- Maps will be dramatically cleaner
- Can move 2x faster safely
- Better obstacle avoidance
- Less CPU usage (LD06 is cleaner, less filtering needed)
- More reliable navigation

## Switching Back to XV-11

If you need to switch back:

**In `launch/launch_robot.launch.py`:**
```python
# Change line 54:
'launch','lidar.launch.py'  # Back to XV-11
# Instead of:
'launch','lidar_ld06.launch.py'
```

Then rebuild and restart.
