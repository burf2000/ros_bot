## Robot Package Template
ALL WAYS DO
Remember to source!!
source install/setup.bash

Build everything
colcon build --symlink-install

To launch for Robot

Fire off launch_sim.launch.py
ros2 run teleop_twist_keyboard  teleop_twist_keyboard 

ros2 launch ros_bot launch_sim.launch.py
ros2 launch ros_bot launch_sim.launch.py world:=./src/ros_bot/worlds/obstacles.world
ros2 launch ros_bot rsp.launch.py use_sim_time:=true


To launch Gazebo
USE A PC!!!!! classic does not work on mac
ros2 launch gazebo_ros gazebo.launch.py
ros2 launch ros_gz_sim gz_sim.launch.py !!!!!

Spawn the bot
ros2 run gazebo_ros spawn_entity.py -topic robot_description -entity ros_bot

Misc
ros2 run joint_state_publisher_gui joint_state_publisher_gui

Show the velcoity etc
ros2 topic echo /cmd_vel

Compression
sudo apt install ros-humble-rqt-image-view
sudo apt install ros-humble-image-transport-plugins

Install Ros2 controller
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-gazebo-ros2-control

If camera is missing compressed or raw run
ros2 run image_transport list_transports
ros2 run image_transport republish compressed raw --ros-args -r in/compressed:=/camera/image_raw/compressed -r out:=/camera/image_raw/uncompressed

On Pi install (camera)
sudo apt install libraspberrypi-bin v4l-utils ros-humble-v4l2-camera

groups (list groups you need to make sure you in video group)
sudo usermod -aG video burf2000

Make sure camera is working
vcgencmd get_camera to check it sees camera
v4l2-ctl --list-devices
Start the Ros Node
ros2 run v4l2_camera v4l2_camera_node --ros-args -p image_size:="[640,480]" -p camera_frame_id:=camera_link_optical

View camera
ros2 run rqt_image_view rqt_image_view

Check voltage on Pi
vcgencmd get_throttled


// to launch ROS gazebo
https://classic.gazebosim.org/tutorials?tut=install_ubuntu&cat=install

https://gazebosim.org/docs/latest/ros2_launch_gazebo/


Depth camera (ros2) Asus xtion
https://github.com/ros-drivers/openni2_camera/issues/144 (READ)
https://github.com/ros-drivers/openni2_camera/tree/iron
https://github.com/mgonzs13/ros2_asus_xtion

Neato lidar
https://github.com/derkaputte/xv_11_driver/tree/main
ros2 run xv_11_driver xv_11_driver --ros-args -p frame_id:=laser_frame -p port:=/dev/ttyACM0
