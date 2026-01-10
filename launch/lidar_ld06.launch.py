import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    package_name = 'ros_bot'

    return LaunchDescription([
        # OKDO Lidar HAT (LD06) - publishes to /scan at ~10Hz (hardware fixed rate)
        # LD06 is much cleaner than XV-11, no filtering needed!
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
                'port_baudrate': 230400,
                'laser_scan_dir': True,  # Set to False if scan direction is reversed
                'enable_angle_crop_func': False,
                'angle_crop_min': 0.0,
                'angle_crop_max': 0.0,
            }]
        )
    ])
