from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

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
        )

        # TODO: Install laser_filters for noise reduction:
        # sudo apt install ros-humble-laser-filters
        # Then uncomment the laser filter node configuration
    ])