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
        # Lidar publishes directly to /scan
        # Laser filtering temporarily disabled until config is fixed
        Node(
            package='xv_11_driver',
            executable='xv_11_driver',
            output='screen',
            parameters=[{
                'port': '/dev/ttyACM0',
                'frame_id': 'laser_frame'
            }]
        )
    ])