import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    package_name = 'ros_bot'
    laser_filter_config = os.path.join(
        get_package_share_directory(package_name),
        'config',
        'laser_filter.yaml'
    )

    return LaunchDescription([
        # XV-11 Lidar Driver - publishes to /scan
        Node(
            package='xv_11_driver',
            executable='xv_11_driver',
            output='screen',
            parameters=[{
                'port': '/dev/ttyACM0',
                'frame_id': 'laser_frame'
            }]
        ),

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