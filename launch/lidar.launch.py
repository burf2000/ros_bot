import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    """
    Lidar launch file - Choose your lidar:
    - XV-11 Neato (old): Use this file
    - OKDO LD06 HAT (new): Use lidar_ld06.launch.py instead

    To switch: Update launch_robot.launch.py to use lidar_ld06.launch.py
    """

    package_name = 'ros_bot'

    return LaunchDescription([
        # XV-11 Lidar Driver - publishes to /scan
        # DISABLED - Using OKDO LD06 instead
        # Uncomment to re-enable XV-11:
        # Node(
        #     package='xv_11_driver',
        #     executable='xv_11_driver',
        #     output='screen',
        #     parameters=[{
        #         'port': '/dev/ttyACM0',
        #         'frame_id': 'laser_frame'
        #     }]
        # ),

        # Scan Cleaner - filters noisy data (0.053m errors) before SLAM
        # Subscribes to /scan, publishes to /scan/filtered
        Node(
            package='ros_bot',
            executable='scan_cleaner.py',
            output='screen',
            parameters=[{
                'min_range': 0.15,  # Filter out <0.15m (includes 0.053m XV-11 noise)
                'max_range': 5.0,
                'input_topic': '/scan',
                'output_topic': '/scan/filtered'
            }]
        )
    ])