# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **ROS2 Humble differential-drive mobile robot** supporting both real hardware (Raspberry Pi 4) and Gazebo simulation. The robot performs autonomous mapping (SLAM Toolbox) and navigation (Nav2) with manual joystick/keyboard control.

**Key Architecture:** Two-machine deployment with robot handling hardware and desktop handling autonomy/visualization.

## Build Commands

```bash
# Build entire workspace
cd ~/dev_ws
colcon build --symlink-install
source install/setup.bash

# Build only this package
colcon build --packages-select ros_bot --symlink-install
source install/setup.bash

# Clean build (if needed)
rm -rf build/ install/ log/
colcon build --packages-select ros_bot --symlink-install
```

**Important:** This is a metapackage with no C++ source - only configs, launch files, and Python scripts. Always use `--symlink-install` for faster iteration on config changes.

## Running the Robot

### Standard Workflow: Real Robot

```bash
# Terminal 1 - Robot (SSH to Pi4):
ssh burf2000@pi4-ros.local
sudo chmod a+rw /dev/ttyUSB0 /dev/ttyACM0
ros2 launch ros_bot launch_robot.launch.py

# Terminal 2 - Desktop (autonomy):
ros2 launch ros_bot desktop.launch.py

# Terminal 3 - Desktop (visualization):
rviz2 -d ~/dev_ws/src/ros_bot/config/main.rviz
```

**Launch Arguments for desktop.launch.py:**
- `slam:=true/false` - Enable SLAM Toolbox (default: true)
- `nav2:=true/false` - Enable Nav2 navigation (default: true)
- `joystick:=true/false` - Enable joystick control (default: true)
- `teleop:=true/false` - Enable keyboard teleop (default: false)
- `rviz:=true/false` - Launch RViz with stack (default: false, better separate)

### Simulation Workflow

```bash
ros2 launch ros_bot launch_sim.launch.py world:=./src/ros_bot/worlds/obstacles.world
ros2 launch ros_bot desktop.launch.py  # In separate terminal
```

## Architecture Overview

### Two-Machine Deployment Model

**Raspberry Pi 4 (Robot-Side)** - `launch_robot.launch.py`:
- Hardware drivers: LiDAR (XV-11), IMU (MPU6050), Camera, Arduino (motors/encoders)
- ROS2 Control: DiffDriveController + JointStateBroadcaster
- Robot Localization EKF: Fuses wheel odometry + IMU → `/odom` frame
- Twist Mux: Arbitrates joystick vs Nav2 commands

**Desktop (Autonomy-Side)** - `desktop.launch.py`:
- SLAM Toolbox: Builds map from `/scan`, publishes `map → odom` transform
- Nav2: Autonomous navigation with local/global planners and costmaps
- RViz: Visualization
- Joystick/Keyboard: Manual control input

### Critical Transform Chain

```
map (SLAM Toolbox)
 ↓
odom (EKF publishes this)
 ↓
base_footprint (diff_drive_controller reference frame)
 ↓
base_link → chassis, wheels, sensors
```

### Data Flow During Navigation

1. **User sets goal** in RViz → Nav2 plans path
2. **Nav2 publishes** `/cmd_vel_nav` command
3. **Twist Mux** (on robot) prioritizes joystick over Nav2 → `/diff_cont/cmd_vel_unstamped`
4. **DiffDriveController** converts to motor commands → Arduino serial
5. **Arduino** returns encoder feedback → `/diff_cont/odom`
6. **EKF** fuses `/diff_cont/odom` + `/imu/corrected` → `/odom` TF
7. **SLAM Toolbox** uses `/scan` + `/odom` TF → updates `/map` + `map → odom` TF
8. **Nav2** uses updated map → replans path (closed loop)

## Key Configuration Files

All configs in `config/` directory:

| File | Purpose | Key Parameters |
|------|---------|----------------|
| `my_controllers.yaml` | Diff drive controller | `wheel_radius: 0.0325`, `wheel_separation: 0.280`, `publish_rate: 50.0` |
| `ekf.yaml` | Sensor fusion (EKF) | `frequency: 10.0`, sensor trust weights, rejection thresholds |
| `mapper_params_online_async.yaml` | SLAM Toolbox | `resolution: 0.05`, `minimum_travel_distance: 0.15`, scan matching penalties |
| `nav2_params.yaml` | Nav2 navigation | Max velocities, acceleration limits, costmap parameters |
| `joystick.yaml` | Joystick mappings | Button/axis assignments, speed scales |
| `twist_mux.yaml` | Command priority | Joystick (priority 100) > Nav2 (priority 10) |

See `Config.md` for comprehensive parameter reference.

## Hardware Specifications

**Robot Dimensions:**
- Chassis: 350×350×100mm
- Wheel diameter: 65mm (radius 32.5mm)
- Wheel separation: 280mm (center-to-center)
- Robot footprint radius: 220mm (for collision avoidance)

**Encoder Calibration:**
- Counts per revolution: 1950 (measured by wheel rotation test)
- Connected via Arduino serial: `/dev/ttyUSB0` @ 57600 baud

**Sensors:**
- LiDAR: XV-11 Neato on `/dev/ttyACM0` → publishes `/scan`
- IMU: MPU6050 via I2C → publishes `/imu` (degrees/sec - non-standard!)
- Camera: USB camera via v4l2

## Critical Implementation Details

### 1. IMU Unit Conversion Required

The MPU6050 driver publishes angular velocity in **degrees/sec** (non-standard!). A custom Python script converts it:

```
/imu (deg/s) → imu_unit_converter.py → /imu/corrected (rad/s)
```

Script location: `scripts/imu_unit_converter.py`

**Always use `/imu/corrected` in EKF config, never raw `/imu`.**

### 2. Severe Wheel Slip Issue

This robot experiences **86% wheel slip during rotation** on smooth floors. Configurations compensate:

**In `ekf.yaml`:**
```yaml
odom0_config: [false, false, false,  # Don't use wheel position
               false, false, false,  # Don't use wheel yaw (slips!)
               true,  true,  false,  # Use wheel linear velocities only
               false, false, true,   # Use wheel angular velocity
               false, false, false]
```

**In `mapper_params_online_async.yaml`:**
```yaml
distance_variance_penalty: 0.1   # Minimal trust in odometry position
angle_variance_penalty: 0.05     # Almost no trust in odometry angles
coarse_search_angle_offset: 0.785  # Large 45° search window
```

### 3. Nav2 Startup Timing

Nav2 requires the `map` frame to exist before starting. SLAM needs time to receive scans and initialize:

```python
delayed_nav2 = TimerAction(
    period=10.0,  # Wait 10 seconds for SLAM
    actions=[nav2_bringup]
)
```

**Never reduce this below 5 seconds or Nav2 will fail with "frame does not exist" errors.**

### 4. Raspberry Pi 4 Performance Tuning

The EKF update rate has been reduced for stable operation:

```yaml
frequency: 10.0  # Was 20Hz, caused "Failed to meet update rate" warnings
sensor_timeout: 0.3
```

### 5. Launch File Dependencies

**launch_robot.launch.py startup sequence:**
1. Robot State Publisher (processes URDF)
2. Hardware drivers start in parallel (LiDAR, IMU, Camera)
3. ROS2 Control delayed 5 seconds (waits for robot_description)
4. Controllers spawned after controller_manager ready

**desktop.launch.py startup sequence:**
1. SLAM Toolbox starts immediately
2. Nav2 delayed 10 seconds (waits for map frame)
3. Joystick/Teleop starts in parallel with SLAM

## Common Development Tasks

### Updating Joystick Mappings

Edit `config/joystick.yaml`:
```yaml
scale_linear:
  x: 0.5  # Normal forward speed (m/s)
scale_linear_turbo:
  x: 1.0  # Turbo speed with RB/R1 held
```

No rebuild needed with `--symlink-install`, just restart launch file.

### Tuning SLAM Performance

Edit `config/mapper_params_online_async.yaml`:

**For cleaner maps (slower):**
```yaml
minimum_travel_distance: 0.25  # Update less frequently
link_match_minimum_response_fine: 0.2  # Stricter scan matching
```

**For faster mapping (noisier):**
```yaml
minimum_travel_distance: 0.10
map_update_interval: 3.0
```

### Adjusting Navigation Speed/Safety

Edit `config/nav2_params.yaml`:

```yaml
controller_server:
  FollowPath:
    max_vel_x: 0.26  # Reduce for safer operation
    max_vel_theta: 1.0

local_costmap:
  robot_radius: 0.22  # Increase for more conservative collision avoidance
  inflation_radius: 0.15  # Larger safety buffer
```

### Debugging TF Issues

```bash
# Check full transform tree
ros2 run tf2_tools view_frames
# Creates frames.pdf - inspect visually

# Check specific transform
ros2 run tf2_ros tf2_echo map base_link

# List all frames
ros2 run tf2_ros tf2_monitor
```

### Checking Sensor Data Flow

```bash
# Verify scan data
ros2 topic hz /scan       # Should be ~5-10 Hz
ros2 topic echo /scan --once

# Verify odometry
ros2 topic hz /diff_cont/odom
ros2 topic hz /odom       # EKF output

# Verify IMU (corrected)
ros2 topic hz /imu/corrected
ros2 topic echo /imu/corrected --once | grep angular_velocity

# Check if SLAM is running
ros2 node list | grep slam_toolbox
ros2 topic hz /map        # Should update periodically
```

## URDF/Xacro Structure

**Main file:** `description/robot.urdf.xacro`

Includes:
- `robot_core.xacro` - Physical robot dimensions, chassis, wheels, joints
- `ros2_control.xacro` - Hardware interface (real robot vs simulation)
- `lidar.xacro` - LiDAR sensor mount and Gazebo plugin
- `camera.xacro` - Camera sensor mount and Gazebo plugin
- `gazebo_control.xacro` - Gazebo differential drive plugin

**To inspect processed URDF:**
```bash
xacro description/robot.urdf.xacro sim_mode:=false > robot.urdf
# View robot.urdf to see expanded XML
```

## Network Configuration

ROS2 uses DDS for multi-machine communication. Ensure:

1. **Same ROS_DOMAIN_ID** on desktop and robot (default: 0)
2. **Network connectivity:** Desktop can ping `pi4-ros.local`
3. **Firewall allows DDS ports** (UDP 7400-7500 typically)

**Test connectivity:**
```bash
# On desktop
ros2 topic list  # Should see robot topics like /diff_cont/odom

# On robot (via SSH)
ros2 topic list  # Should see desktop topics like /cmd_vel_nav
```

## Critical Files to Never Modify Without Testing

1. **`description/ros2_control.xacro`** - Hardware interface config
   - `enc_counts_per_rev: 1950` is measured value, don't change casually

2. **`config/ekf.yaml`** - Sensor fusion tuning
   - Carefully tuned for this robot's wheel slip characteristics

3. **`scripts/imu_unit_converter.py`** - IMU unit conversion
   - Critical for correct gyro readings

4. **`launch/launch_robot.launch.py`** - Robot startup sequence
   - Timing dependencies are carefully orchestrated

## Joystick Control Reference

**Dead man's switch:** Button 6 (LB/L1) MUST be held to move robot
**Turbo:** Button 7 (RB/R1) doubles speed while held
**Left stick vertical:** Forward/backward
**Left stick horizontal:** Rotation

Default speeds (in `config/joystick.yaml`):
- Normal linear: 0.5 m/s
- Turbo linear: 1.0 m/s
- Normal angular: 2.0 rad/s
- Turbo angular: 4.0 rad/s

## Simulation vs Real Robot Differences

**Hardware Interface:**
- Real: `diffdrive_arduino/DiffDriveArduinoHardware` (Arduino serial)
- Sim: `gz_ros2_control/GazeboSimSystem` (Gazebo physics)

**Sensor Plugins:**
- Real: External drivers (xv_11_driver, mpu6050driver, v4l2_camera)
- Sim: Gazebo plugins (gpu_lidar, imu_sensor, camera)

**Launch Detection:**
- Uses `sim_mode` argument in URDF to switch configs
- Set via `use_sim_time` launch argument

## Git Branches

- `main` - Stable branch
- `feature/odom` - Current development (odometry calibration work)

**Current uncommitted changes:** `config/main.rviz` has modifications

## External Package Dependencies

**Robot (Pi4) requires:**
- `diffdrive_arduino` - Custom Arduino hardware interface
- `mpu6050driver` - MPU6050 IMU driver (publishes non-standard units!)
- `xv_11_driver` - XV-11 Neato LiDAR driver

**Desktop requires:**
- `slam_toolbox` - Online async SLAM
- `navigation2` / `nav2_bringup` - Autonomous navigation
- `robot_localization` - EKF sensor fusion

**Install commands documented in README.md**

## Performance Characteristics

**Update Rates:**
- Controller manager: 30 Hz
- DiffDriveController odometry: 50 Hz
- EKF: 10 Hz (reduced for Pi4 stability)
- Local costmap: 5 Hz
- Global costmap: 1 Hz
- SLAM map updates: 5 seconds

**Computational Load:**
- Pi4 typically runs at 40-60% CPU with all drivers
- EKF warnings if >10Hz update rate attempted
- SLAM consumes most desktop CPU during active mapping

## Known Limitations

1. **Wheel slip during rotation** - 86% on smooth floors, compensated in configs
2. **IMU gyro noise** - MPU6050 has significant drift, strict filtering applied
3. **LiDAR noise** - XV-11 has random noise points (laser filter disabled currently)
4. **No dynamic obstacles** - Nav2 configured for static environments
5. **Limited speed** - Max 0.26 m/s linear, 1.0 rad/s angular for stability

## Testing Robot After Changes

**Minimal test sequence:**
```bash
# 1. Build
colcon build --packages-select ros_bot
source install/setup.bash

# 2. Start robot (SSH to Pi4)
ros2 launch ros_bot launch_robot.launch.py

# 3. Check basics (on desktop)
ros2 topic list  # Verify topics appear
ros2 topic hz /scan  # Verify LiDAR working
ros2 topic hz /diff_cont/odom  # Verify encoders working
ros2 run tf2_ros tf2_monitor  # Verify transforms

# 4. Manual control test
ros2 launch ros_bot desktop.launch.py joystick:=true nav2:=false slam:=false
# Move robot with joystick, verify responsive

# 5. SLAM test
ros2 launch ros_bot desktop.launch.py
# Drive around, check map builds in RViz

# 6. Nav2 test
# Set initial pose in RViz (2D Pose Estimate)
# Click navigation goal (2D Goal Pose)
# Verify robot navigates autonomously
```

## Configuration Documentation

For detailed parameter explanations and tuning guidance, see:
- **Config.md** - Comprehensive configuration reference with all parameters
- **README.md** - User guide with workflows and commands

Both files are kept up-to-date and should be consulted before modifying configs.
