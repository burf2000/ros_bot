"""
launch_robot_slam.launch.py
---------------------------
Same as launch_robot.launch.py but also brings up slam_toolbox on the robot
so /map and the map->odom TF are published locally and become available to
any consumer over the ROS2 graph (e.g. the burf_platform_driver bridge).

Use this instead of launch_robot.launch.py when the robot must produce its
own map (e.g. for the Burf Platform browser map view) rather than relying
on the desktop machine to run SLAM.

Run:
    ros2 launch ros_bot launch_robot_slam.launch.py
    ros2 launch ros_bot launch_robot_slam.launch.py slam:=false   # equivalent to launch_robot.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    package_name = 'ros_bot'

    use_slam_arg = DeclareLaunchArgument(
        'slam',
        default_value='true',
        description='Whether to launch slam_toolbox alongside the robot stack'
    )

    use_slam = LaunchConfiguration('slam')

    # Base robot stack: rsp, twist_mux, lidar, camera, ros2_control + spawners.
    base_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory(package_name),
                'launch',
                'launch_robot.launch.py'
            )
        ])
    )

    # SLAM Toolbox - online async (mirrors desktop.launch.py's configuration).
    slam_params_file = os.path.join(
        get_package_share_directory(package_name),
        'config',
        'mapper_params_online_async.yaml'
    )

    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('slam_toolbox'),
                'launch',
                'online_async_launch.py'
            )
        ]),
        launch_arguments={
            'slam_params_file': slam_params_file,
            'use_sim_time': 'false'
        }.items(),
        condition=IfCondition(use_slam)
    )

    # Delay SLAM by a few seconds so the lidar + controller_manager are up
    # before slam_toolbox starts subscribing to /scan and looking up TF.
    delayed_slam = TimerAction(period=8.0, actions=[slam_toolbox])

    return LaunchDescription([
        use_slam_arg,
        base_robot,
        delayed_slam,
    ])
