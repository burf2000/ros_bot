import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    """
    Lightweight desktop launch for visualization only.
    Use this when you just want to view robot data without SLAM/Nav2.
    """

    package_name = 'ros_bot'

    # Launch arguments
    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value='main.rviz',
        description='RViz config file name (main.rviz, drive_bot.rviz, BOW.rviz, etc.)'
    )

    rviz_config = LaunchConfiguration('rviz_config')

    # RViz2
    rviz_config_file = [
        os.path.join(get_package_share_directory(package_name), 'config', ''),
        rviz_config
    ]

    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen'
    )

    # Teleop keyboard
    # NOTE: Run in separate terminal manually if needed:
    #   ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_cont/cmd_vel_unstamped
    teleop_keyboard = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        output='screen',
        remappings=[('/cmd_vel', '/diff_cont/cmd_vel_unstamped')]
    )

    # Image viewer (optional - shows camera feed)
    rqt_image_view = Node(
        package='rqt_image_view',
        executable='rqt_image_view',
        name='rqt_image_view',
        output='screen'
    )

    return LaunchDescription([
        rviz_config_arg,
        rviz2,
        teleop_keyboard,
        rqt_image_view
    ])
