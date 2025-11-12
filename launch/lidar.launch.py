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
        # Lidar publishes scan data directly to /scan
        Node(
            package='xv_11_driver',
            executable='xv_11_driver',
            output='screen',
            parameters=[{
                'port': '/dev/ttyACM0',
                'frame_id': 'laser_frame'
            }]
        ),

        # TODO: Install laser_filters package, then enable this:
        # sudo apt install ros-humble-laser-filters
        #
        # # Laser scan filter cleans up noise
        # # Reads /scan_raw, outputs /scan (for SLAM and Nav2)
        # Node(
        #     package='laser_filters',
        #     executable='scan_to_scan_filter_chain',
        #     output='screen',
        #     parameters=[laser_filter_config],
        #     remappings=[
        #         ('/scan', '/scan'),           # Output
        #         ('/scan_raw', '/scan_raw')    # Input
        #     ]
        # )
    ])