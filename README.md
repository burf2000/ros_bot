## Robot Package Template

To launch for Robot

Fire off launch_sim.launch.py
ros2 launch ros_bot launch_sim.launch.py
ros2 launch ros_bot launch_sim.launch.py world:=./src/ros_bot/worlds/obstacles.world


ros2 launch ros_bot rsp.launch.py use_sim_time:=true


To launch Gazebo
ros2 launch gazebo_ros gazebo.launch.py

Spawn the bot
ros2 run gazebo_ros spawn_entity.py -topic robot_description -entity ros_bot





Misc
ros2 run joint_state_publisher_gui joint_state_publisher_gui


Show the velcoity etc
ros2 topic echo /cmd_vel