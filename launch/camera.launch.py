import os

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """Camera bring-up.

    MEASURED ON THE ROBOT, 2026-10-06 — do not "optimise" this without re-measuring:

        raw device capture (v4l2-ctl, ROS stopped) ..... 30.0 fps
        /image_raw, no subscriber ...................... 29.6 fps
        /image_raw, ONE remote subscriber over WiFi .... 10.0 fps
        /image_raw, OLO WebRTC worker attached .......... 3.0 fps

    THE CAMERA IS NOT THE PROBLEM. /image_raw is 640x480 yuv422 = 614 KB per
    frame, published RELIABLE (the v4l2_camera default; it exposes no QoS
    override for this topic). A REMOTE subscriber therefore back-pressures the
    publisher and the CAMERA ITSELF is throttled — every other consumer is
    slowed too, including anything running locally. 30 fps of raw is roughly
    147 Mbit/s, which WiFi will not carry.

    So: off-board consumers (the OLO appliance's video worker, the Burf
    Platform ros2 driver) MUST subscribe to `/image_raw/compressed`
    (~39 KB/frame, ~9 Mbit/s at 30 fps), never `/image_raw`. If the video feed
    looks like a slideshow, check `ros2 topic hz /image_raw` on the robot
    first: under ~10 fps means something off-board is pulling raw frames.
    """

    return LaunchDescription([

        Node(
            package='v4l2_camera',
            executable='v4l2_camera_node',
            output='screen',
            # The node exits if it cannot open the device — which happens at
            # boot, when the camera is not always ready as the stack comes up
            # (same race as the lidar). Without respawn the robot comes up with
            # no camera at all and nothing restarts it.
            respawn=True,
            respawn_delay=5,
            parameters=[{
                'image_size': [640, 480],
                'output_encoding': 'yuv422_yuy2',
                'camera_frame_id': 'camera_link_optical',
            }]
        )
    ])
