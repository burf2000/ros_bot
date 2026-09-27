# AMCL Localization Guide

This guide explains how to save maps created with SLAM Toolbox and use them with AMCL for localization-only navigation.

## Overview

There are two modes of operation:

1. **SLAM Mode** (default `desktop.launch.py`) - Creates new maps while navigating
2. **Localization Mode** (AMCL) - Uses a pre-built map for navigation

AMCL (Adaptive Monte Carlo Localization) is faster and more stable than SLAM when you already have a good map of your environment.

---

## Step 1: Create a Map with SLAM

First, build a map using the standard workflow:

```bash
# Terminal 1 - Robot (SSH to Pi4):
ssh burf2000@pi4-ros.local
ros2 launch ros_bot launch_robot.launch.py

# Terminal 2 - Desktop (SLAM + Nav2):
ros2 launch ros_bot desktop.launch.py

# Terminal 3 - Desktop (visualization):
rviz2 -d ~/dev_ws/src/ros_bot/config/main.rviz
```

Drive the robot around to map your environment using the joystick.

---

## Step 2: Save the Map

Once you have a complete map, save it using one of these methods:

### Method A: Command Line (Recommended)

```bash
# Save map to the maps directory
ros2 run nav2_map_server map_saver_cli -f ~/dev_ws/src/ros_bot/maps/my_map

# Or with a timestamp
ros2 run nav2_map_server map_saver_cli -f ~/dev_ws/src/ros_bot/maps/map_$(date +%Y-%m-%d)
```

This creates two files:
- `my_map.yaml` - Map metadata (resolution, origin, thresholds)
- `my_map.pgm` - Map image (grayscale: white=free, black=occupied, gray=unknown)

### Method B: RViz2 SLAM Toolbox Plugin

1. In RViz2, find the SLAM Toolbox panel
2. Enter a filename in the "Save Map" field
3. Click "Save Map"

### Method C: Service Call

```bash
ros2 service call /map_saver/save_map nav2_msgs/srv/SaveMap "{map_topic: /map, map_url: '~/dev_ws/src/ros_bot/maps/my_map', image_format: 'pgm', map_mode: 'trinary', free_thresh: 0.25, occupied_thresh: 0.65}"
```

---

## Step 3: Verify the Map

Check that your map was saved correctly:

```bash
# List saved maps
ls -la ~/dev_ws/src/ros_bot/maps/

# View the map image (optional)
eog ~/dev_ws/src/ros_bot/maps/my_map.pgm

# Check the YAML metadata
cat ~/dev_ws/src/ros_bot/maps/my_map.yaml
```

The YAML file should look like:
```yaml
image: my_map.pgm
mode: trinary
resolution: 0.05
origin: [-1.23, -4.56, 0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
```

---

## Step 4: Run AMCL Localization

Use the localization launch file with your saved map:

```bash
# Terminal 1 - Robot (SSH to Pi4):
ssh burf2000@pi4-ros.local
ros2 launch ros_bot launch_robot.launch.py

# Terminal 2 - Desktop (AMCL + Nav2):
ros2 launch ros_bot localization.launch.py map:=~/dev_ws/src/ros_bot/maps/my_map.yaml

# Terminal 3 - Desktop (visualization):
rviz2 -d ~/dev_ws/src/ros_bot/config/main.rviz
```

### Launch Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `map` | (required) | Full path to map YAML file |
| `nav2` | `true` | Launch Nav2 navigation stack |
| `joystick` | `true` | Enable joystick control |
| `rviz` | `false` | Launch RViz (better to run separately) |
| `autostart` | `true` | Auto-start lifecycle nodes |

Examples:
```bash
# Basic localization with navigation
ros2 launch ros_bot localization.launch.py map:=~/dev_ws/src/ros_bot/maps/my_map.yaml

# Localization only (no Nav2, just joystick control)
ros2 launch ros_bot localization.launch.py map:=~/dev_ws/src/ros_bot/maps/my_map.yaml nav2:=false

# With RViz included
ros2 launch ros_bot localization.launch.py map:=~/dev_ws/src/ros_bot/maps/my_map.yaml rviz:=true
```

---

## Step 5: Set Initial Pose

AMCL needs to know where the robot starts. In RViz2:

1. Click the **"2D Pose Estimate"** button in the toolbar
2. Click on the map where the robot is located
3. Drag to indicate the robot's orientation
4. Release - AMCL will converge on the correct position

Alternatively, you can set the initial pose programmatically:
```bash
ros2 topic pub /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{
  header: {frame_id: 'map'},
  pose: {
    pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}},
    covariance: [0.25, 0, 0, 0, 0, 0,
                 0, 0.25, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0.0685]
  }
}" --once
```

---

## Step 6: Navigate

Once localized, you can send navigation goals:

1. **RViz2**: Click "2D Goal Pose" and click on the map
2. **Command Line**:
   ```bash
   ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 2.0}, orientation: {w: 1.0}}}}"
   ```

---

## Troubleshooting

### AMCL not converging
- Drive the robot around slowly to help AMCL match laser scans to the map
- Increase `max_particles` in the config (default: 2000)
- Check that the map matches the current environment

### "Transform timeout" errors
- Ensure robot launch file is running on the Pi4
- Check network connectivity: `ping pi4-ros.local`
- Verify clocks are synchronized: `timedatectl status` on both machines

### Map doesn't load
- Check the full path is correct
- Verify both `.yaml` and `.pgm` files exist
- Check file permissions: `ls -la ~/dev_ws/src/ros_bot/maps/`

### Robot not moving
- Check Nav2 lifecycle: `ros2 lifecycle list /controller_server`
- Verify costmaps are updating in RViz2
- Check `/cmd_vel_nav` topic is publishing

---

## SLAM vs AMCL Comparison

| Feature | SLAM Toolbox | AMCL |
|---------|-------------|------|
| Map required | No (creates map) | Yes |
| CPU usage | Higher | Lower |
| Localization accuracy | Good | Excellent (with good map) |
| Handles map changes | Yes | Limited |
| Best for | Exploration, mapping | Repeated navigation |

---

## File Locations

- **Maps**: `~/dev_ws/src/ros_bot/maps/`
- **AMCL config**: `~/dev_ws/src/ros_bot/config/amcl_params.yaml`
- **Nav2 config**: `~/dev_ws/src/ros_bot/config/nav2_params.yaml`
- **Launch file**: `~/dev_ws/src/ros_bot/launch/localization.launch.py`
