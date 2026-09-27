"""
Localization Launch File for ros_bot

Launches AMCL-based localization with a pre-built map.
Use this instead of desktop.launch.py when you have a saved map
and want localization-only navigation (no SLAM).

Usage:
    ros2 launch ros_bot localization.launch.py map:=/path/to/map.yaml

See docs/AMCL_LOCALIZATION.md for detailed instructions.
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition

from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    package_name = 'ros_bot'
    bringup_dir = get_package_share_directory(package_name)

    # Launch arguments
    map_yaml_file = LaunchConfiguration('map')
    use_nav2 = LaunchConfiguration('nav2')
    use_joystick = LaunchConfiguration('joystick')
    use_rviz = LaunchConfiguration('rviz')
    autostart = LaunchConfiguration('autostart')
    rviz_config = LaunchConfiguration('rviz_config')

    # Paths to config files
    amcl_params_file = os.path.join(bringup_dir, 'config', 'amcl_params.yaml')
    nav2_params_file = os.path.join(bringup_dir, 'config', 'nav2_params.yaml')

    # Lifecycle nodes for localization
    lifecycle_nodes = ['map_server', 'amcl']

    # Substitutions for AMCL params
    param_substitutions = {
        'use_sim_time': 'false',
        'yaml_filename': map_yaml_file
    }

    configured_amcl_params = RewrittenYaml(
        source_file=amcl_params_file,
        param_rewrites=param_substitutions,
        convert_types=True
    )

    # TF remappings
    remappings = [('/tf', 'tf'), ('/tf_static', 'tf_static')]

    # =====================
    # Launch Arguments
    # =====================

    declare_map_arg = DeclareLaunchArgument(
        'map',
        description='Full path to map yaml file to load (required)'
    )

    declare_nav2_arg = DeclareLaunchArgument(
        'nav2',
        default_value='true',
        description='Whether to launch Nav2 navigation stack'
    )

    declare_joystick_arg = DeclareLaunchArgument(
        'joystick',
        default_value='true',
        description='Whether to launch joystick control'
    )

    declare_rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='false',
        description='Whether to launch RViz2 (better to run separately)'
    )

    declare_autostart_arg = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the localization stack'
    )

    declare_rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value='main.rviz',
        description='RViz config file name'
    )

    # =====================
    # Localization Nodes
    # =====================

    # Map Server - serves the pre-built map
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[configured_amcl_params],
        remappings=remappings
    )

    # AMCL - localization using particle filter
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[configured_amcl_params],
        remappings=remappings
    )

    # Lifecycle Manager for Localization
    lifecycle_manager_localization = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[
            {'use_sim_time': False},
            {'autostart': autostart},
            {'node_names': lifecycle_nodes}
        ]
    )

    # =====================
    # Navigation (Nav2)
    # =====================

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

    # Delay Nav2 to let AMCL initialize first
    delayed_nav2 = TimerAction(
        period=5.0,
        actions=[nav2_bringup]
    )

    # =====================
    # Joystick Control
    # =====================

    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(bringup_dir, 'launch', 'joystick.launch.py')
        ]),
        launch_arguments={'use_sim_time': 'false'}.items(),
        condition=IfCondition(use_joystick)
    )

    # =====================
    # RViz2 (optional)
    # =====================

    rviz_config_file = [
        os.path.join(bringup_dir, 'config', ''),
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

    # =====================
    # Launch Description
    # =====================

    return LaunchDescription([
        # Environment
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        # Arguments
        declare_map_arg,
        declare_nav2_arg,
        declare_joystick_arg,
        declare_rviz_arg,
        declare_autostart_arg,
        declare_rviz_config_arg,

        # Localization stack (AMCL + Map Server)
        map_server,
        amcl,
        lifecycle_manager_localization,

        # Navigation (delayed)
        delayed_nav2,

        # Input devices
        joystick,

        # Visualization
        rviz2,
    ])
