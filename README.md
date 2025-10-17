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

### SSH into the Robot
```bash
ssh burf2000@pi4-ros.local
```

### On the Robot
```bash
sudo chmod a+rw /dev/ttyUSB0
sudo chmod a+rw /dev/ttyACM0
ros2 launch ros_bot launch_robot.launch.py

ros2 launch mpu9250driver mpu9250driver_launch.py
ros2 run xv_11_driver xv_11_driver --ros-args -p frame_id:=laser_frame -p port:=/dev/ttyACM0
ros2 launch ros_bot camera.launch
# OR
ros2 run v4l2_camera v4l2_camera_node --ros-args -p image_size:="[640,480]" -p camera_frame_id:=camera_link_optical
```

### On the Desktop
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
