import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    return LaunchDescription([

        Node(
            package='xv_11_driver',
            executable='xv_11_driver',
            output='screen',
            parameters=[{
                'serial_port': '/dev/ttyACM0',
                'frame_id': 'laser_frame'
            }]
        )
    ])