"""
launch_slam_mode.launch.py
--------------------------
Brings up slam_toolbox in EITHER mapping OR localization mode, chosen at launch
time from an intent file the Burf Platform driver writes:

    ~/maps/.slam_intent.json   ->  {"mode": "mapping"}                  (build a fresh map)
                                   {"mode": "localization",
                                    "map": "/home/burf2000/maps/kitchen"} (localise against a saved map)

This is run by its OWN systemd unit (ros-slam.service), SEPARATE from the
sensor/base stack (ros-robot.service runs launch_robot_slam.launch.py slam:=false).
That separation is what lets the driver switch slam mode by just restarting
ros-slam.service — without bouncing the lidar/camera/controllers.

Safe default: if the intent file is missing or unreadable, comes up in MAPPING
mode, i.e. exactly today's behaviour. So a plain boot is unchanged.

Mapping mode  -> slam_toolbox online_async_launch + mapper_params_online_async.yaml
Localization  -> slam_toolbox localization_launch + mapper_params_localization.yaml
                 with map_file_name rewritten to the intent's map basename.
"""
import os
import json
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def _read_intent():
    """Return (mode, map_basename). Defaults to mapping on any problem."""
    path = os.path.expanduser('~/maps/.slam_intent.json')
    try:
        with open(path) as f:
            d = json.load(f)
        mode = str(d.get('mode', 'mapping')).strip().lower()
        if mode not in ('mapping', 'localization'):
            mode = 'mapping'
        return mode, d.get('map')
    except Exception:
        return 'mapping', None


def _localization_params(pkg_share, map_basename):
    """Write a temp localization params file with map_file_name set to the
    intent's map (slam_toolbox appends .posegraph/.data). Returns its path,
    or None if the saved map doesn't exist (caller falls back to mapping)."""
    template = os.path.join(pkg_share, 'config', 'mapper_params_localization.yaml')
    if not map_basename or not os.path.exists(map_basename + '.posegraph'):
        return None
    import re
    s = open(template).read()
    # Replace whatever map_file_name line is there with the requested map.
    s = re.sub(r'map_file_name:\s*\S+', 'map_file_name: ' + map_basename, s, count=1)
    out = '/tmp/slam_localization_active.yaml'
    with open(out, 'w') as f:
        f.write(s)
    return out


def generate_launch_description():
    pkg_share = get_package_share_directory('ros_bot')
    slam_share = get_package_share_directory('slam_toolbox')
    mode, map_basename = _read_intent()

    loc_params = _localization_params(pkg_share, map_basename) if mode == 'localization' else None

    if mode == 'localization' and loc_params:
        slam = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(slam_share, 'launch', 'localization_launch.py')),
            launch_arguments={
                'slam_params_file': loc_params,
                'use_sim_time': 'false',
            }.items(),
        )
    else:
        # mapping (or localization requested but map missing -> safe fallback)
        slam = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(slam_share, 'launch', 'online_async_launch.py')),
            launch_arguments={
                'slam_params_file': os.path.join(
                    pkg_share, 'config', 'mapper_params_online_async.yaml'),
                'use_sim_time': 'false',
            }.items(),
        )

    return LaunchDescription([slam])
