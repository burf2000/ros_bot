# ROSBot (pi4-ros)

A two-wheeled diff-drive robot: Arduino motor/encoder board over serial, OKDO LD06 LiDAR, MPU6050 IMU and a
Pi camera, on a Raspberry Pi 4. The same package runs the real robot, the desktop SLAM/Nav2 stack and a
Gazebo simulation.

| Where | ROS 2 | Workspace |
|---|---|---|
| Robot (Pi 4, `pi4-ros.local`) | Humble | `~/dev_ws` |
| Desktop / skynet | Jazzy | `~/dev_ws` or `~/ros2_ws` |
| ROS2 Lab (browser, skynet) | Jazzy | `~/ros2_ws` (domain 87 sandbox) |

Always source the workspace first, and build from its root:

```bash
source install/setup.bash
colcon build --symlink-install            # or: --packages-select ros_bot
```

---

## 1. The real robot

**Start the robot first, then the desktop.** Autostart is off, so after a reboot nothing runs until you
launch it.

On the robot:
```bash
ssh burf2000@pi4-ros.local
sudo chmod a+rw /dev/ttyUSB0 /dev/ttyACM0     # Arduino + LiDAR
ros2 launch ros_bot launch_robot.launch.py
```

This starts:
- `robot_state_publisher` (robot model and TF)
- ros2_control + `diff_cont` (wheels and encoders; publishes `odom → base_footprint` itself)
- `twist_mux` (joystick / teleop / Nav2 → `/diff_cont/cmd_vel_unstamped`)
- the LD06 LiDAR (`/scan`, about 10 Hz; see `docs/OKDO_LD06_SETUP.md`)
- the MPU6050 IMU
- the camera (`/camera/image_raw`, plus `/compressed`)

There is **no EKF on the robot**. Wheel slip is about 0.5%, so `diff_cont` publishes odometry directly to
save Pi CPU.

Wait for `Loaded diff_cont` before starting the desktop.

On the Burf Platform the robot instead runs `launch_robot_slam.launch.py slam:=false` (the base stack), plus
`launch_slam_mode.launch.py` in its own service. That one picks mapping or localization from
`~/maps/.slam_intent.json`, which the Platform driver writes.

## 2. The desktop (SLAM + Nav2 + joystick)

```bash
ros2 launch ros_bot desktop.launch.py
```

| Option | Default | |
|---|---|---|
| `slam:=` | `true` | slam_toolbox, a fresh map every launch |
| `nav2:=` | `true` | Nav2, ready for goals once there is a map |
| `joystick:=` | `true` | gamepad (see below) |
| `teleop:=` | `false` | keyboard teleop instead |
| `rviz:=` | `false` | RViz with `config/main.rviz` |

Common runs:
```bash
ros2 launch ros_bot desktop.launch.py rviz:=true                    # with RViz
ros2 launch ros_bot desktop.launch.py nav2:=false                   # mapping only
ros2 launch ros_bot desktop.launch.py joystick:=false teleop:=true   # keyboard
ros2 launch ros_bot desktop_viz.launch.py                           # just look (no SLAM/Nav2)
rviz2 -d src/ros_bot/config/main.rviz                               # RViz on its own
```

Then:
1. Drive around to build the map.
2. In RViz, set **2D Pose Estimate**.
3. Send **2D Goal Pose**, and Nav2 drives there.

### Saving and reusing a map
```bash
# slam_toolbox (keeps the pose graph, so you can continue mapping later)
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: '/home/burf2000/dev_ws/my_map'}"
# plain image + yaml
ros2 run nav2_map_server map_saver_cli -f ~/dev_ws/my_map
```

To localise against a saved map, use `config/mapper_params_localization.yaml` (mode `localization`, set
`map_file_name`), or let the Platform do it through `launch_slam_mode.launch.py`. AMCL is an alternative;
see `docs/AMCL_LOCALIZATION.md` and `launch/localization.launch.py`.

## 3. Simulation (Gazebo)

Uses the current Gazebo (Harmonic, through `ros_gz_sim`), **not** Gazebo Classic. On Jazzy, which is what
skynet and the ROS2 Lab run:

```bash
ros2 launch ros_bot launch_sim.launch.py                                          # empty world
ros2 launch ros_bot launch_sim.launch.py world:=./src/ros_bot/worlds/obstacles.world
```

This opens three windows:
- **Gazebo**, with the robot spawned.
- **RViz** (`config/drive_bot.rviz`, fixed to `odom`): the robot, its LiDAR hits and the camera.
- **Robot Steering**: sliders for speed and turn. Drag them, or click `+`, `-`, `<`, `>` and Stop. It
  publishes `Twist` on `/cmd_vel` into `twist_mux`. Leave **stamped** unticked.

Behind them:
- ros2_control **inside Gazebo** (the `gz_ros2_control` plugin), with `diff_cont` and `joint_broad`.
- the joystick and `twist_mux`. There is no EKF, as on the real robot: `diff_cont` publishes `odom → base_footprint`.
- the ROS↔Gazebo bridge for `/clock`, `/scan` and the camera.

Everything runs with `use_sim_time`.

| Option | Default | |
|---|---|---|
| `world:=` | `worlds/empty.world` | e.g. `./src/ros_bot/worlds/obstacles.world` |
| `rviz:=` | `true` | RViz |
| `rviz_config:=` | `drive_bot.rviz` | use `main.rviz` once SLAM is running (it is fixed to `map`) |
| `steering:=` | `true` | the slider drive window |

Other ways to drive it:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard        # keyboard, on /cmd_vel
# or a gamepad: hold button 6 (see Joystick below)
```

Running two simulations at once? Gazebo ignores `ROS_DOMAIN_ID`, so also give each one its own
`GZ_PARTITION` (for example `export GZ_PARTITION=me`). Otherwise the two Gazebos fight over the same robot.

Map and navigate in sim. Run these yourself, because `desktop.launch.py` is fixed to real time:
```bash
ros2 launch slam_toolbox online_async_launch.py slam_params_file:=./src/ros_bot/config/mapper_params_online_async.yaml use_sim_time:=true
ros2 launch nav2_bringup navigation_launch.py params_file:=./src/ros_bot/config/nav2_params.yaml use_sim_time:=true
rviz2 -d src/ros_bot/config/main.rviz --ros-args -p use_sim_time:=true
```

Sim needs `ros-jazzy-ros-gz`, `ros-jazzy-gz-ros2-control`, `ros-jazzy-twist-mux`,
`ros-jazzy-twist-stamper`, `ros-jazzy-robot-localization`, `ros-jazzy-joy` / `teleop-twist-joy` and
`ros-jazzy-rqt-robot-steering`.

Just the model, no physics:
```bash
ros2 launch ros_bot rsp.launch.py
ros2 run joint_state_publisher_gui joint_state_publisher_gui
```

## 4. Joystick

- Hold **button 6** (LB / L1): the dead-man switch. Nothing moves without it.
- **Left stick:**
  - vertical = forward/back, 0.25 m/s
  - horizontal = turn, 0.5 rad/s
- Hold **button 7** (RB / R1) for turbo: 0.5 m/s and 1.0 rad/s.

```bash
ros2 topic echo /joy              # raw stick data
ros2 topic echo /cmd_vel_joy      # what the joystick asks for
```

Keyboard teleop: `i` forward, `,` back, `j`/`l` turn, `k` stop, `q`/`z` speed up or down.

## 5. Topics and command chain

```
joystick → /cmd_vel_joy ┐
teleop   → /cmd_vel     ├→ twist_mux → /diff_cont/cmd_vel_unstamped → diff_cont (Humble)
Nav2     → /cmd_vel_nav ┘                                          → twist_stamper → /diff_cont/cmd_vel (Jazzy)
```

`twist_mux` priorities: joystick 100 > tracker 20 > Nav2 10 > teleop 5 (`config/twist_mux.yaml`).

Handy commands:
```bash
ros2 topic list / echo / hz / info --verbose <topic>
ros2 control list_controllers
ros2 control list_hardware_interfaces
ros2 run rqt_image_view rqt_image_view
ros2 run image_transport republish compressed raw --ros-args -r in/compressed:=/camera/image_raw/compressed -r out:=/camera/image_raw/uncompressed
```

## 6. Setup

Robot (Pi 4, Humble):
```bash
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-twist-mux ros-humble-xacro libserial-dev
sudo apt install libraspberrypi-bin v4l-utils ros-humble-v4l2-camera ros-humble-image-transport-plugins
sudo usermod -aG video,tty,dialout burf2000
sudo apt remove brltty            # it grabs the CH340/Arduino serial port
```
Drivers: [diff-drive_arduino](https://github.com/joshnewans/diff-drive_arduino),
[serial](https://github.com/joshnewans/serial), [ros2_mpu6050_driver](https://github.com/hiwad-aziz/ros2_mpu6050_driver),
and the LD06 setup in `docs/OKDO_LD06_SETUP.md`.

Desktop (Jazzy):
```bash
sudo apt install ros-jazzy-slam-toolbox ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-robot-localization \
  ros-jazzy-teleop-twist-keyboard ros-jazzy-teleop-twist-joy ros-jazzy-joy ros-jazzy-twist-mux ros-jazzy-twist-stamper \
  ros-jazzy-ros-gz ros-jazzy-gz-ros2-control ros-jazzy-rqt-robot-steering ros-jazzy-rqt-image-view ros-jazzy-image-transport-plugins
```

Key parameters (encoder counts, wheel size, controller rates) are listed in `Config.md`.

## 7. Troubleshooting

- **Nothing runs after a reboot:** autostart is off, so launch it by hand (section 1).
- **`/dev/ttyUSB0` or `/dev/ttyACM0` permission denied:** run the `chmod` above, or add yourself to `dialout`/`tty`.
- **Robot ignores commands:** check `ros2 control list_controllers` shows `diff_cont` active, and that the
  dead-man button is held.
- **Sim on Jazzy, robot doesn't move:** `twist_mux` must run with `use_stamped: false`, which `launch_sim`
  sets. Otherwise `/cmd_vel_joy` ends up carrying both `Twist` and `TwistStamped`.
- **Camera frame rate drops:** only subscribe to `/camera/image_raw/compressed` across the network (see the
  note in `launch/camera.launch.py`).
