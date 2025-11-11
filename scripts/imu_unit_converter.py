#!/usr/bin/env python3
"""
IMU Unit Converter Node

The MPU6050 driver publishes angular_velocity in degrees/second instead of
the ROS standard radians/second. This node converts the units and republishes.

Subscribes: /imu (sensor_msgs/Imu) - degrees/sec from driver
Publishes: /imu/corrected (sensor_msgs/Imu) - radians/sec (ROS standard)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import math


class ImuUnitConverter(Node):
    def __init__(self):
        super().__init__('imu_unit_converter')

        # Conversion factor: degrees to radians
        self.deg_to_rad = math.pi / 180.0

        # Publisher for corrected IMU data
        self.pub = self.create_publisher(Imu, '/imu/corrected', 10)

        # Subscriber to raw IMU data
        self.sub = self.create_subscription(
            Imu,
            '/imu',
            self.imu_callback,
            10)

        self.get_logger().info('IMU Unit Converter started')
        self.get_logger().info('Converting angular_velocity from degrees/sec to radians/sec')
        self.get_logger().info('Input: /imu  Output: /imu/corrected')

    def imu_callback(self, msg):
        # Create a copy of the message
        corrected_msg = Imu()

        # Copy header
        corrected_msg.header = msg.header

        # Copy orientation (unchanged - quaternion is already unitless)
        corrected_msg.orientation = msg.orientation
        corrected_msg.orientation_covariance = msg.orientation_covariance

        # Convert angular_velocity from degrees/sec to radians/sec
        corrected_msg.angular_velocity.x = msg.angular_velocity.x * self.deg_to_rad
        corrected_msg.angular_velocity.y = msg.angular_velocity.y * self.deg_to_rad
        corrected_msg.angular_velocity.z = msg.angular_velocity.z * self.deg_to_rad

        # Copy angular_velocity_covariance (unchanged - it's a scaling factor)
        corrected_msg.angular_velocity_covariance = msg.angular_velocity_covariance

        # Copy linear_acceleration (unchanged - already in m/s²)
        corrected_msg.linear_acceleration = msg.linear_acceleration
        corrected_msg.linear_acceleration_covariance = msg.linear_acceleration_covariance

        # Publish corrected message
        self.pub.publish(corrected_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ImuUnitConverter()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
