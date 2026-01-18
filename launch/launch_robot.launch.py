import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessStart

from launch_ros.actions import Node



def generate_launch_description():


    # Include the robot_state_publisher launch file, provided by our own package. Force sim time to be enabled
    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!

    package_name='ros_bot' #<--- CHANGE ME

    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'false', 'use_ros2_control': 'true'}.items()
    )

    # Robot Localization EKF - DISABLED
    # EKF not needed: wheel traction is good (~0.5% slip), IMU was disabled anyway
    # DiffDriveController now publishes odom->base_footprint transform directly (enable_odom_tf: true)
    # This reduces Pi4 CPU load and eliminates a potential bottleneck
    # ekf_config_path = os.path.join(get_package_share_directory(package_name),'config','ekf.yaml')
    # robot_localization_node = Node(
    #     package='robot_localization',
    #     executable='ekf_node',
    #     name='ekf_filter_node',
    #     output='screen',
    #     parameters=[ekf_config_path]
    # )

    twist_mux_params = os.path.join(get_package_share_directory(package_name),'config','twist_mux.yaml')
    twist_mux = Node(
            package="twist_mux",
            executable="twist_mux",
            parameters=[twist_mux_params],
            remappings=[('/cmd_vel_out','/diff_cont/cmd_vel_unstamped')]
        )

    # Lidar launch - OKDO LD06 HAT
    # LD06 hardware scans at fixed ~10Hz (motor speed), cannot be changed
    # SLAM/Nav2 configured to handle 10Hz efficiently
    lidar = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','lidar_ld06.launch.py'
                )])
    )

    # IMU disabled for OLO - wheel odometry tracks well (~0.5% slip)
    # and IMU was causing high CPU usage on Pi4
    # imu = IncludeLaunchDescription(
    #             PythonLaunchDescriptionSource([os.path.join(
    #                 get_package_share_directory("mpu6050driver"),'launch','mpu6050driver_launch.py'
    #             )])
    # )

    # IMU unit converter: converts angular_velocity from degrees/sec to radians/sec
    # Disabled - not needed when IMU is disabled
    # imu_converter = Node(
    #     package='ros_bot',
    #     executable='imu_unit_converter.py',
    #     name='imu_unit_converter',
    #     output='screen'
    # )

    camera = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','camera.launch.py'
                )])
    )


    robot_description = Command(['ros2 param get --hide-type /robot_state_publisher robot_description'])

    controller_params_file = os.path.join(get_package_share_directory(package_name),'config','my_controllers.yaml')

    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[{'robot_description': robot_description},
                    controller_params_file]
    )

    delayed_controller_manager = TimerAction(period=5.0, actions=[controller_manager])

    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"],
    )

    delayed_diff_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=controller_manager,
            on_start=[diff_drive_spawner],
        )
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],
    )

    delayed_joint_broad_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=controller_manager,
            on_start=[joint_broad_spawner],
        )
    )

    # Launch them all!
    return LaunchDescription([
        rsp,
        twist_mux,
        lidar,
        # imu,                      # Disabled - high CPU on Pi4, not needed with good wheel traction
        # imu_converter,            # Disabled - not needed when IMU is disabled
        camera,
        # robot_localization_node,  # Disabled - DiffDriveController publishes odom TF directly
        delayed_controller_manager,
        delayed_diff_drive_spawner,
        delayed_joint_broad_spawner
    ])
