import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    package_name = 'ros_bot'

    return LaunchDescription([
        # OKDO Lidar HAT (LD06) - publishes to /scan
        Node(
            package='ldlidar_stl_ros2',
            executable='ldlidar_stl_ros2_node',
            name='LD06',
            output='screen',
            parameters=[{
                'product_name': 'LDLiDAR_LD06',
                'topic_name': 'scan',
                'frame_id': 'laser_frame',
                'port_name': '/dev/ttyAMA0',  # UART on Pi GPIO 14/15 (try /dev/ttyS0 if this doesn't work)
                'serial_baudrate': 230400,
                'laser_scan_dir': True,  # Set to False if scan direction is reversed
                'enable_angle_crop_func': False,
                'angle_crop_min': 0.0,
                'angle_crop_max': 0.0,
            }]
        ),

        # Scan Cleaner - filters any remaining noise
        # Even though LD06 is much cleaner than XV-11, still useful for safety
        Node(
            package='ros_bot',
            executable='scan_cleaner.py',
            output='screen',
            parameters=[{
                'min_range': 0.05,  # LD06 min is 2cm, but filter below 5cm for safety
                'max_range': 12.0,  # LD06 max range
                'input_topic': '/scan',
                'output_topic': '/scan/filtered'
            }]
        )
    ])
