# ROSBot Configuration Reference

Quick reference guide for key configuration parameters across the project.

---

## Hardware Configuration

### `description/ros2_control.xacro`
| Parameter | Value | Description |
|-----------|-------|-------------|
| `enc_counts_per_rev` | 1950 | Encoder counts per wheel revolution (verified by measurement) |
| `loop_rate` | 30 | Hardware interface update rate (Hz) |
| `device` | /dev/ttyUSB0 | Arduino serial port |
| `baud_rate` | 57600 | Arduino serial communication speed |

---

## Differential Drive Controller

### `config/my_controllers.yaml`
| Parameter | Value | Description |
|-----------|-------|-------------|
| `wheel_separation` | 0.280 | Distance between wheel centers (meters) |
| `wheel_radius` | 0.0325 | Wheel radius - 65mm diameter wheels (meters) |
| `publish_rate` | 50.0 | Odometry publishing frequency (Hz) |
| `update_rate` | 30 | Controller manager update rate (Hz) |
| `pose_covariance_diagonal[5]` | 1.0 | Yaw uncertainty - high due to wheel slip |
| `twist_covariance_diagonal[5]` | 1.0 | Angular velocity uncertainty |
| `enable_odom_tf` | false | Let EKF publish odom→base_footprint transform |

---

## Sensor Fusion (EKF)

### `config/ekf.yaml`
| Parameter | Value | Description |
|-----------|-------|-------------|
| `frequency` | 10.0 | EKF update rate - reduced for Pi4 performance (Hz) |
| `sensor_timeout` | 0.3 | Time before sensor data considered stale (seconds) |
| `two_d_mode` | true | Constrain to 2D plane (ignore z-axis) |
| `odom0` | /diff_cont/odom | Wheel odometry topic |
| `odom0_config[5]` | false | Don't use wheel yaw (slips during rotation) |
| `odom0_config[6:8]` | true, true | Use wheel linear velocities (x, y) |
| `odom0_config[11]` | true | Use wheel angular velocity (yaw_dot) |
| `imu0` | /imu/corrected | IMU topic (after unit conversion) |
| `imu0_config[11]` | true | Use IMU angular velocity (yaw_dot) |
| `imu0_twist_rejection_threshold` | 0.3 | Strict rejection of noisy gyro readings |
| `smooth_lagged_data` | true | Smooth sensor data to reduce noise |
| `history_length` | 1.0 | Keep 1 second history for smoothing |

---

## SLAM Toolbox

### `config/mapper_params_online_async.yaml`
| Parameter | Value | Description |
|-----------|-------|-------------|
| `mode` | mapping | Mapping mode (vs localization) |
| `resolution` | 0.05 | Map grid resolution (5cm cells) |
| `min_laser_range` | 0.1 | Minimum valid lidar range (meters) |
| `max_laser_range` | 5.0 | Maximum valid lidar range (meters) |
| `map_update_interval` | 5.0 | Map update interval (seconds) |
| `minimum_travel_distance` | 0.15 | Min movement to update map (meters) |
| `minimum_travel_heading` | 0.15 | Min rotation to update map (~8.5°) |
| `distance_variance_penalty` | 0.1 | Low trust in odometry position |
| `angle_variance_penalty` | 0.05 | Very low trust in odometry angles (86% wheel slip!) |
| `coarse_search_angle_offset` | 0.785 | Large angle search window (45°) due to unreliable odometry |
| `do_loop_closing` | true | Enable loop closure for map consistency |
| `link_match_minimum_response_fine` | 0.1 | Minimum quality for scan matching |

---

## Navigation (Nav2)

### `config/nav2_params.yaml`

#### Controller Server
| Parameter | Value | Description |
|-----------|-------|-------------|
| `controller_frequency` | 20.0 | Control loop frequency (Hz) |
| `max_vel_x` | 0.26 | Maximum linear velocity (m/s) |
| `max_vel_theta` | 1.0 | Maximum angular velocity (rad/s) |
| `acc_lim_x` | 2.5 | Linear acceleration limit (m/s²) |
| `acc_lim_theta` | 3.2 | Angular acceleration limit (rad/s²) |
| `xy_goal_tolerance` | 0.25 | Goal position tolerance (meters) |
| `yaw_goal_tolerance` | 0.25 | Goal orientation tolerance (radians) |

#### Local Costmap
| Parameter | Value | Description |
|-----------|-------|-------------|
| `update_frequency` | 5.0 | Costmap update rate (Hz) |
| `width` | 3 | Costmap width (meters) |
| `height` | 3 | Costmap height (meters) |
| `resolution` | 0.05 | Costmap cell size (5cm) |
| `robot_radius` | 0.22 | Robot footprint radius (meters) |
| `rolling_window` | true | Costmap follows robot |
| `raytrace_max_range` | 3.0 | Clear obstacles up to 3m when lidar sees through them |
| `obstacle_max_range` | 2.5 | Mark new obstacles up to 2.5m away |

#### Global Costmap
| Parameter | Value | Description |
|-----------|-------|-------------|
| `update_frequency` | 1.0 | Costmap update rate (Hz) |
| `global_frame` | map | Fixed world frame |
| `track_unknown_space` | true | Track unexplored areas |
| `inflation_radius` | 0.15 | Safety buffer around obstacles (meters) |

---

## Joystick Control

### `config/joystick.yaml`
| Parameter | Value | Description |
|-----------|-------|-------------|
| `scale_linear.x` | 0.5 | Normal forward speed (m/s) |
| `scale_linear_turbo.x` | 1.0 | Turbo forward speed (m/s) |
| `scale_angular.yaw` | 2.0 | Normal turning speed (rad/s) |
| `scale_angular_turbo.yaw` | 4.0 | Turbo turning speed (rad/s) |
| `enable_button` | 6 | Dead man's switch button (LB/L1) |
| `enable_turbo_button` | 7 | Turbo button (RB/R1) |
| `axis_linear.x` | 1 | Left stick vertical axis |
| `axis_angular.yaw` | 0 | Left stick horizontal axis |
| `require_enable_button` | true | Must hold enable to move (safety) |

---

## Lidar Filtering

### `config/laser_filter.yaml`
| Filter | Key Parameter | Description |
|--------|---------------|-------------|
| `range_filter` | 0.1 - 5.0m | Remove points outside valid range |
| `speckle_filter` | max_range_difference: 0.1 | Remove isolated points >10cm from neighbors |
| `median_filter` | window_size: 5 | Smooth by taking median of 5 points |
| `temporal_filter` | temporal_window: 3 | Average over 3 scans to remove blips |

---

## Launch Configuration

### `launch/desktop.launch.py`
| Argument | Default | Description |
|----------|---------|-------------|
| `slam` | true | Launch SLAM Toolbox for mapping |
| `nav2` | true | Launch Nav2 navigation stack (delayed 5s) |
| `rviz` | false | Launch RViz (better to run separately) |
| `joystick` | true | Enable joystick control |
| `teleop` | false | Enable keyboard teleop |

---

## Robot Physical Specifications

| Measurement | Value | Notes |
|-------------|-------|-------|
| Wheel Diameter | 65mm | Verified measurement |
| Wheel Separation | 280mm | Center-to-center distance |
| Robot Radius | 220mm | For collision avoidance |
| Encoder CPR | 1950 | Counts per wheel revolution (measured) |

---

## Known Issues & Calibration Notes

1. **Wheel Slip During Rotation**: 86% slip on smooth floors
   - SLAM configured to not trust odometry angles
   - EKF does not use wheel yaw orientation

2. **EKF Performance**: Reduced to 10Hz for stable operation on Pi4
   - Was 20Hz, caused "Failed to meet update rate" warnings

3. **Nav2 Startup**: 5-second delay after SLAM
   - Prevents "frame does not exist" errors
   - Gives SLAM time to create map frame

4. **Lidar Filtering**: Mandatory for XV-11 Neato lidar
   - High noise without filtering
   - Dramatically improves map quality

5. **IMU Gyro**: Smoothing and strict filtering enabled
   - MPU6050 has significant noise
   - Units converted from deg/s to rad/s

---

## Quick Tuning Guide

**To improve map quality:**
- Decrease `minimum_travel_distance` (updates more frequently)
- Increase `link_match_minimum_response_fine` (stricter scan matching)
- Adjust laser filter thresholds

**To improve navigation safety:**
- Increase `robot_radius` (more conservative)
- Increase `inflation_radius` (larger safety buffer)
- Decrease `max_vel_x` and `max_vel_theta` (slower, safer)

**To reduce CPU load:**
- Decrease `controller_frequency`
- Decrease `update_frequency` on costmaps
- Decrease `ekf frequency`

**To improve odometry:**
- Calibrate `enc_counts_per_rev` with wheel rotation test
- Measure and verify `wheel_radius` and `wheel_separation`
- Check for mechanical issues (wheel slip, loose encoders)

---

## File Locations Summary

```
config/
├── ekf.yaml                              # Sensor fusion
├── mapper_params_online_async.yaml       # SLAM settings
├── nav2_params.yaml                      # Navigation
├── my_controllers.yaml                   # Diff drive controller
├── joystick.yaml                         # Joystick control
├── laser_filter.yaml                     # Lidar filtering
└── twist_mux.yaml                        # Command velocity multiplexing

description/
├── ros2_control.xacro                    # Hardware interface
└── robot_core.xacro                      # Robot dimensions

launch/
├── launch_robot.launch.py                # Robot-side launch (Pi4)
├── desktop.launch.py                     # Desktop-side launch
├── lidar.launch.py                       # Lidar + filtering
└── joystick.launch.py                    # Joystick control
```
