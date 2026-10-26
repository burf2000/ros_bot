import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node



def generate_launch_description():


    # Include the robot_state_publisher launch file, provided by our own package. Force sim time to be enabled
    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!

    package_name='ros_bot' #<--- CHANGE ME

    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'true', 'use_ros2_control': 'true'}.items()
    )

    joystick = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','joystick.launch.py'
                )]), launch_arguments={'use_sim_time': 'true'}.items()
    )

    twist_mux_params = os.path.join(get_package_share_directory(package_name),'config','twist_mux.yaml')
    twist_mux = Node(
            package="twist_mux",
            executable="twist_mux",
            parameters=[twist_mux_params, {'use_sim_time': True, 'use_stamped': False}],  # Jazzy's twist_mux defaults to TwistStamped; our teleop/joystick send Twist (twist_stamper adds the stamp for diff_cont)
            remappings=[('/cmd_vel_out','/diff_cont/cmd_vel_unstamped')]
        )

    # No EKF in sim, to match the real robot (launch_robot.launch.py has it off): diff_cont publishes
    # odom->base_footprint itself (enable_odom_tf: true), and a second publisher of the same transform
    # (the EKF, publish_tf: true) made RViz jump between the two. Nav2 reads /diff_cont/odom directly.


    default_world = os.path.join(
        get_package_share_directory(package_name),
        'worlds',
        'empty.world'
        )    
    
    world = LaunchConfiguration('world')

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=default_world,
        description='World to load'
        )

    # Gazebo server and GUI as SEPARATE processes. Started together ('gz sim <world>'), a GUI that hangs on
    # start-up (seen in the ROS2 Lab) also stops the server: no /clock, no robot, RViz at ROS time 0.
    # Split, the simulation, ros2_control, RViz and the steering window run even if the Gazebo window is
    # slow or never appears; gui:=false skips it entirely (lighter, and fine with RViz).
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]),
                    launch_arguments={'gz_args': ['-s -r -v2 ', world], 'on_exit_shutdown': 'true'}.items()
             )
    gui_arg = DeclareLaunchArgument('gui', default_value='true', description='Open the Gazebo window')
    gazebo_gui = ExecuteProcess(
        cmd=['gz', 'sim', '-g', '-v2'],
        condition=IfCondition(LaunchConfiguration('gui')),
        output='screen'
    )

    # Run the spawner node from the ros_gz_sim package. The entity name doesn't really matter if you only have a single robot.
    spawn_entity = Node(package='ros_gz_sim', executable='create',
                        arguments=['-topic', 'robot_description',
                                   '-name', 'my_bot',
                                   '-z', '0.1'],
                        output='screen')


    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"],
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],
    )

    # No standalone controller_manager in sim: the gz_ros2_control plugin that the robot
    # description loads in sim_mode (description/ros2_control.xacro) runs one inside Gazebo,
    # and the spawners below talk to that. A second ros2_control_node here also used
    # `ros2 param get /robot_state_publisher robot_description`, which races robot_state_publisher
    # and aborts the whole launch (the same bug launch_robot.launch.py fixed in #6).


    bridge_params = os.path.join(get_package_share_directory(package_name),'config','gz_bridge.yaml')
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ]
    )

    ros_gz_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/camera/image_raw"]
    )



    # Code for delaying a node (I haven't tested how effective it is)
    # 
    # First add the below lines to imports
    # from launch.actions import RegisterEventHandler
    # from launch.event_handlers import OnProcessExit
    #
    # Then add the following below the current diff_drive_spawner
    # delayed_diff_drive_spawner = RegisterEventHandler(
    #     event_handler=OnProcessExit(
    #         target_action=spawn_entity,
    #         on_exit=[diff_drive_spawner],
    #     )
    # )
    #
    # Replace the diff_drive_spawner in the final return with delayed_diff_drive_spawner



    # RViz, on by default. drive_bot.rviz is fixed to odom (robot, LiDAR, camera), which works without a map;
    # use rviz_config:=main.rviz once slam_toolbox is running.
    rviz_arg = DeclareLaunchArgument('rviz', default_value='true', description='Start RViz')
    rviz_config_arg = DeclareLaunchArgument('rviz_config', default_value='drive_bot.rviz',
                                            description='RViz config in ros_bot/config')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', PathJoinSubstitution([get_package_share_directory(package_name), 'config',
                                               LaunchConfiguration('rviz_config')])],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen'
    )


    # Slider drive GUI (rqt_robot_steering), on by default. It publishes geometry_msgs/Twist on /cmd_vel, the
    # teleop input of twist_mux (joystick and Nav2 win on priority, see config/twist_mux.yaml). Leave its
    # "stamped" box unticked: a TwistStamped on /cmd_vel would clash with keyboard teleop.
    steering_arg = DeclareLaunchArgument('steering', default_value='true', description='Start the slider drive GUI')
    steering = Node(
        package='rqt_robot_steering',
        executable='rqt_robot_steering',   # the topic is set in its window (default /cmd_vel); no positional args
        condition=IfCondition(LaunchConfiguration('steering')),
        output='screen'
    )


    # Launch them all!
    return LaunchDescription([
        rsp,
        joystick,
        twist_mux,
        world_arg,
        gazebo,
        gui_arg,
        gazebo_gui,
        spawn_entity,
        diff_drive_spawner,
        joint_broad_spawner,
        ros_gz_bridge,
        ros_gz_image_bridge,
        rviz_arg,
        rviz_config_arg,
        rviz,
        steering_arg,
        steering
    ])
