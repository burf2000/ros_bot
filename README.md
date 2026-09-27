# 🦾 ROSBot Setup & Usage Guide

## 🚀 Robot Package Template

### Always Remember
Before doing anything, **source your workspace**:

```bash
source install/setup.bash
```

### Build Everything
From the root of your workspace:

```bash
colcon build --symlink-install
```

---

## 🤖 Running the Robot

⚠️ **IMPORTANT**: Always start the robot **BEFORE** launching the desktop stack!

---

## 🗺️ Default Workflow: Map → Navigate

### **Standard Usage (One Launch, Map + Navigate)**

**On Robot (Pi4):**
```bash
ssh burf2000@pi4-ros.local
sudo chmod a+rw /dev/ttyUSB0 /dev/ttyACM0
ros2 launch ros_bot launch_robot.launch.py
```

**On Desktop:**
```bash
# Launch everything with defaults (SLAM + Nav2 + Joystick, no RViz)
ros2 launch ros_bot desktop.launch.py
```

**Default behavior:**
- ✅ SLAM Toolbox running (fresh map every time)
- ✅ Nav2 running (ready for goals once map is built)
- ✅ Joystick enabled
- ❌ RViz disabled (launch separately if needed)
- ❌ Keyboard teleop disabled

**Usage:**
1. **Drive around with joystick** to build map
2. **Open RViz** in separate terminal: `rviz2 -d ~/dev_ws/src/ros_bot/config/main.rviz`
3. **Set initial pose** in RViz (2D Pose Estimate)
4. **Send navigation goals** (2D Goal Pose)
5. Robot navigates autonomously!

**No need to save/load maps** - fresh map every launch!

---

### **Optional: Saving Your Map (For Persistence)**

If you want to save a map for reuse:

```bash
# Option 1: Save using SLAM Toolbox service
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: '/home/burf2000/dev_ws/my_map'}"

# Option 2: Save using map_server (traditional way)
ros2 run nav2_map_server map_saver_cli -f ~/dev_ws/my_map
```

This creates:
- `my_map.pgm` - Map image
- `my_map.yaml` - Map metadata
- `my_map.posegraph` - SLAM graph (for continuing mapping)
- `my_map.data` - SLAM data (for continuing mapping)

---

### **Workflow 3: Navigation with Saved Map**

Use this when you have a map and want autonomous navigation.

**First, update SLAM config to use your saved map:**
```bash
# Edit the SLAM config
nano ~/dev_ws/src/ros_bot/config/mapper_params_online_async.yaml

# Uncomment and set the map file:
# map_file_name: /home/burf2000/dev_ws/my_map
# map_start_at_dock: true

# Or change mode to localization:
# mode: localization  # Instead of mapping
```

**Then rebuild:**
```bash
cd ~/dev_ws
colcon build --packages-select ros_bot --symlink-install
source install/setup.bash
```

**Launch with Nav2:**
```bash
# Full navigation stack (SLAM in localization mode + Nav2)
ros2 launch ros_bot desktop.launch.py slam:=true nav2:=true joystick:=true teleop:=false rviz:=true
```

**Set initial pose in RViz:**
1. Click "2D Pose Estimate" button
2. Click on map where robot is
3. Drag to set orientation

**Send navigation goals:**
1. Click "2D Goal Pose" button
2. Click destination on map
3. Robot navigates autonomously!

---

## 📋 Quick Reference: Desktop Launch Commands

| Task | Command |
|------|---------|
| **🚀 Default workflow** (map + navigate) | `ros2 launch ros_bot desktop.launch.py` |
| **With RViz** (to see the map) | `ros2 launch ros_bot desktop.launch.py rviz:=true` |
| **Just mapping** (no Nav2) | `ros2 launch ros_bot desktop.launch.py nav2:=false` |
| **Keyboard instead of joystick** | `ros2 launch ros_bot desktop.launch.py joystick:=false teleop:=true` |
| **Save map** | `ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: '/home/burf2000/dev_ws/my_map'}"` |
| **Just visualization** | `ros2 launch ros_bot desktop.launch.py slam:=false nav2:=false rviz:=true` |

**Default parameters:** `slam:=true`, `nav2:=true`, `joystick:=true`, `rviz:=false`, `teleop:=false`

**Robot always runs the same command:**
```bash
ros2 launch ros_bot launch_robot.launch.py
```

---

## 🎮 Joystick Controls

**How to use:**
1. **Hold Enable Button** (Button 6 - usually LB/L1 shoulder button)
2. **Move left stick** to drive:
   - **Vertical** (Axis 1): Forward/Backward (0.25 m/s normal, 0.5 m/s turbo)
   - **Horizontal** (Axis 0): Turn left/right (0.5 rad/s normal, 1.0 rad/s turbo)
3. **Hold Turbo Button** (Button 7 - usually RB/R1) for faster speeds

**Dead Man's Switch:** You MUST hold the enable button to move (safety feature!)

**Test your joystick:**
```bash
# See raw joystick data
ros2 topic echo /joy

# See velocity commands being sent
ros2 topic echo /cmd_vel_joy
```

**Keyboard Controls** (if using `teleop:=true`):
- `i` - Forward
- `,` - Backward
- `j` - Turn left
- `l` - Turn right
- `k` - Stop
- `q/z` - Increase/decrease speeds

---



### Step 1: SSH into the Robot
```bash
ssh burf2000@pi4-ros.local
```

### Step 2: Launch Robot (On Pi4)
```bash
sudo chmod a+rw /dev/ttyUSB0 /dev/ttyACM0
ros2 launch ros_bot launch_robot.launch.py
```

This launches:
- ✅ Wheel encoders (diff_drive_controller)
- ✅ IMU (mpu6050driver)
- ✅ LiDAR (xv_11_driver)
- ✅ Camera
- ✅ **robot_localization EKF** (sensor fusion)
- ✅ TF publishers (`odom → base_footprint`)

Wait until you see: `[controller_manager]: Loaded diff_cont` and `[ekf_filter_node]: ...`

### Step 3: Launch Desktop (On Your Computer)

**🚀 Standard Workflow (Map + Navigate):**
```bash
# Launch with defaults: SLAM + Nav2 + Joystick (no RViz)
ros2 launch ros_bot desktop.launch.py
```

**Then open RViz separately (optional):**
```bash
rviz2 -d ~/dev_ws/src/ros_bot/config/main.rviz
```

**Workflow:**
1. Drive around with joystick to build map
2. Once happy with map, send Nav2 goals in RViz
3. Robot navigates autonomously!

**Optional Variants:**
```bash
# With RViz included
ros2 launch ros_bot desktop.launch.py rviz:=true

# No joystick (use keyboard instead)
ros2 launch ros_bot desktop.launch.py joystick:=false teleop:=true

# Just mapping (no Nav2)
ros2 launch ros_bot desktop.launch.py nav2:=false

# Just visualization
ros2 launch ros_bot desktop_viz.launch.py
```

**📋 Manual Way (Individual Components):**
```bash
ros2 launch slam_toolbox online_async_launch.py   slam_params_file:=./src/ros_bot/config/mapper_params_online_async.yaml   use_sim_time:=false

ros2 launch nav2_bringup navigation_launch.py   params_file:=./src/ros_bot/config/nav2_params.yaml   use_sim_time:=false

ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_cont/cmd_vel_unstamped

rviz2 -d src/ros_bot/config/main.rviz
ros2 run rqt_image_view rqt_image_view
```

---

## 🧠 Simulation Mode

### Run the Simulation
```bash
ros2 launch ros_bot launch_sim.launch.py world:=./src/ros_bot/worlds/obstacles.world

ros2 launch slam_toolbox online_async_launch.py   slam_params_file:=./src/ros_bot/config/mapper_params_online_async.yaml   use_sim_time:=true

ros2 launch nav2_bringup navigation_launch.py   params_file:=./src/ros_bot/config/nav2_params.yaml   use_sim_time:=true

ros2 run teleop_twist_keyboard teleop_twist_keyboard

rviz2 -d src/ros_bot/config/main.rviz
```

---

## 📡 Useful ROS2 Commands

### Topics
```bash
ros2 topic list
ros2 topic echo /topic_name
ros2 topic info /topic_name --verbose
ros2 topic hz /topic_name
ros2 topic pub /topic_name std_msgs/msg/String "data: 'Message'"
```

### ROS2 Control
```bash
ros2 control list_controllers
ros2 control list_hardware_components
ros2 control list_hardware_interfaces
```

### Teleop
Old way:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

New way (mapped topic):
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_cont/cmd_vel_unstamped
```

---

## 🧩 Launch Shortcuts

### Desktop (SLAM + Nav2 + Joystick)
```bash
# 🚀 Default: Map + Navigate workflow (SLAM + Nav2 + Joystick, no RViz)
ros2 launch ros_bot desktop.launch.py

# Then open RViz separately:
rviz2 -d ~/dev_ws/src/ros_bot/config/main.rviz

# Or include RViz in launch:
ros2 launch ros_bot desktop.launch.py rviz:=true

# Keyboard instead of joystick:
ros2 launch ros_bot desktop.launch.py joystick:=false teleop:=true

# Just mapping (no Nav2):
ros2 launch ros_bot desktop.launch.py nav2:=false

# Visualization only (lightweight):
ros2 launch ros_bot desktop_viz.launch.py
```

### Simulation
```bash
ros2 launch ros_bot launch_sim.launch.py world:=./src/ros_bot/worlds/obstacles.world
ros2 launch ros_bot launch_sim.launch.py
ros2 launch ros_bot rsp.launch.py use_sim_time:=true
```

### Robot
```bash
ros2 launch ros_bot launch_robot.launch.py
```

### Gazebo
> ⚠️ Use a PC — Gazebo Classic does not work on macOS.

```bash
ros2 launch gazebo_ros gazebo.launch.py
ros2 launch ros_gz_sim gz_sim.launch.py
```

### RViz
```bash
rviz2 -d src/ros_bot/config/main.rviz
```

### Spawn the Bot
```bash
ros2 run gazebo_ros spawn_entity.py -topic robot_description -entity ros_bot
```

### Misc
```bash
ros2 run joint_state_publisher_gui joint_state_publisher_gui
ros2 topic echo /cmd_vel
```

---

## 🧰 Installation & Setup

### Desktop Dependencies
```bash
sudo apt install ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup
sudo apt install ros-humble-robot-localization
sudo apt install ros-humble-teleop-twist-keyboard
```

### Compression Tools
```bash
sudo apt install ros-humble-rqt-image-view
sudo apt install ros-humble-image-transport-plugins
```

### ROS2 Control
```bash
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-gazebo-ros2-control
# On Pi:
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers
```

### Spawners
```bash
ros2 control list_hardware_interfaces
ros2 run controller_manager spawner diff_cont
ros2 run controller_manager spawner joint_broad
```

### Image Transport
```bash
ros2 run image_transport list_transports
ros2 run image_transport republish compressed raw   --ros-args -r in/compressed:=/camera/image_raw/compressed   -r out:=/camera/image_raw/uncompressed
```

---

## 📸 Camera Setup (Pi)

```bash
sudo apt install libraspberrypi-bin v4l-utils ros-humble-v4l2-camera
sudo usermod -aG video burf2000
vcgencmd get_camera
v4l2-ctl --list-devices

ros2 run v4l2_camera v4l2_camera_node --ros-args   -p image_size:="[640,480]" -p camera_frame_id:=camera_link_optical

ros2 launch ros_bot camera.launch
ros2 run rqt_image_view rqt_image_view
```

Check Pi voltage:
```bash
vcgencmd get_throttled
```

---

## 🌐 References & Drivers

### IMU
- https://github.com/hiwad-aziz/ros2_mpu6050_driver


### Gazebo
- [Classic Gazebo Install Guide](https://classic.gazebosim.org/tutorials?tut=install_ubuntu&cat=install)
- [ROS2 + Gazebo Docs](https://gazebosim.org/docs/latest/ros2_launch_gazebo/)

### Depth Camera (Asus Xtion)
- [openni2_camera Issue #144](https://github.com/ros-drivers/openni2_camera/issues/144)
- [openni2_camera (Iron)](https://github.com/ros-drivers/openni2_camera/tree/iron)
- [ros2_asus_xtion](https://github.com/mgonzs13/ros2_asus_xtion)

### Neato Lidar
- [xv_11_driver Repo](https://github.com/derkaputte/xv_11_driver/tree/main)
```bash
ros2 run xv_11_driver xv_11_driver --ros-args -p frame_id:=laser_frame -p port:=/dev/ttyACM0
```

---

## 🔧 Additional Setup

### For Raspberry Pi
```bash
sudo apt install ros-humble-twist-mux libserial-dev ros-humble-xacro
```

Repos:
- https://github.com/joshnewans/serial  
- https://github.com/joshnewans/diff-drive_arduino

List serial devices:
```bash
ls /dev/tty*
ls /dev/serial
ls /dev/serial/by-id
```

---

## ⚠️ Troubleshooting

### Humble Issues
```bash
# spawner.py renamed to spawner
sudo apt remove brltty  # Removes conflicting package
```

### USB Permissions
```bash
sudo usermod -a -G tty burf2000
```

---

## 🎮 Joystick Support
```bash
sudo apt install joystick jstest-gtk evtest
evtest
ros2 run joy joy_enumerate_devices
ros2 run joy joy_node
ros2 run joy_tester test_joy
```

---

## 🗺️ SLAM Toolbox
```bash
sudo apt install ros-humble-slam-toolbox
ros2 launch slam_toolbox online_async_launch.py   slam_params_file:=./src/ros_bot/config/mapper_params_online_async.yaml
```

---

## 🧭 Navigation (Nav2)
```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-turtlebot3*
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true
```

### TwistMux (Combine Joystick + Nav2 Topics)
```bash
sudo apt install ros-humble-twist-mux
ros2 run twist_mux twist_mux --ros-args   --params-file ./src/ros_bot/config/twist_mux.yaml   -r cmd_vel_out:=diff_cont/cmd_vel_unstamped
```
