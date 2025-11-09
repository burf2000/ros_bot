import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition

from launch_ros.actions import Node


def generate_launch_description():

    package_name = 'ros_bot'

    # Launch arguments
    use_slam_arg = DeclareLaunchArgument(
        'slam',
        default_value='true',
        description='Whether to launch SLAM Toolbox'
    )

    use_nav2_arg = DeclareLaunchArgument(
        'nav2',
        default_value='true',
        description='Whether to launch Nav2'
    )

    use_rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Whether to launch RViz2'
    )

    use_teleop_arg = DeclareLaunchArgument(
        'teleop',
        default_value='true',
        description='Whether to launch teleop_twist_keyboard'
    )

    use_joystick_arg = DeclareLaunchArgument(
        'joystick',
        default_value='true',
        description='Whether to launch joystick control (joystick runs on desktop only)'
    )

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value='main.rviz',
        description='RViz config file name (main.rviz, drive_bot.rviz, BOW.rviz, etc.)'
    )

    # Get launch configurations
    use_slam = LaunchConfiguration('slam')
    use_nav2 = LaunchConfiguration('nav2')
    use_rviz = LaunchConfiguration('rviz')
    use_teleop = LaunchConfiguration('teleop')
    use_joystick = LaunchConfiguration('joystick')
    rviz_config = LaunchConfiguration('rviz_config')

    # SLAM Toolbox launch
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

    # Nav2 launch
    nav2_params_file = os.path.join(
        get_package_share_directory(package_name),
        'config',
        'nav2_params.yaml'
    )

    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('nav2_bringup'),
                'launch',
                'navigation_launch.py'
            )
        ]),
        launch_arguments={
            'params_file': nav2_params_file,
            'use_sim_time': 'false'
        }.items(),
        condition=IfCondition(use_nav2)
    )

    # RViz2 launch
    rviz_config_file = [
        os.path.join(get_package_share_directory(package_name), 'config', ''),
        rviz_config
    ]

    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen',
        condition=IfCondition(use_rviz)
    )

    # Teleop keyboard (runs in same terminal - press keys to control robot)
    # NOTE: To run teleop in a separate terminal manually, use:
    #   ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_cont/cmd_vel_unstamped
    teleop_keyboard = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        output='screen',
        remappings=[('/cmd_vel', '/diff_cont/cmd_vel_unstamped')],
        condition=IfCondition(use_teleop)
    )

    # Joystick control (if joystick is plugged into desktop)
    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory(package_name),
                'launch',
                'joystick.launch.py'
            )
        ]),
        launch_arguments={'use_sim_time': 'false'}.items(),
        condition=IfCondition(use_joystick)
    )

    # Launch all
    return LaunchDescription([
        use_slam_arg,
        use_nav2_arg,
        use_rviz_arg,
        use_teleop_arg,
        use_joystick_arg,
        rviz_config_arg,
        slam_toolbox,
        nav2_bringup,
        rviz2,
        teleop_keyboard,
        joystick
    ])
