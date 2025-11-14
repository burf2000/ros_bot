#!/usr/bin/env python3
"""
Scan Cleaner Node - Filters noisy lidar data before SLAM processes it.

Subscribes to /scan (raw XV-11 data) and publishes /scan/filtered with:
- Readings below 0.15m replaced with inf (out of range)
- Readings above 5.0m replaced with inf
- This removes the 0.053m noise from robot body reflections

The XV-11 outputs 0.053m as an error value for invalid readings.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math


class ScanCleaner(Node):
    def __init__(self):
        super().__init__('scan_cleaner')

        # Parameters
        self.declare_parameter('min_range', 0.15)  # Filter out <0.15m (includes 0.053m noise)
        self.declare_parameter('max_range', 5.0)   # Filter out >5.0m
        self.declare_parameter('input_topic', '/scan')
        self.declare_parameter('output_topic', '/scan/filtered')

        self.min_range = self.get_parameter('min_range').value
        self.max_range = self.get_parameter('max_range').value
        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value

        # Subscriber and Publisher
        self.subscription = self.create_subscription(
            LaserScan,
            input_topic,
            self.scan_callback,
            10
        )

        self.publisher = self.create_publisher(
            LaserScan,
            output_topic,
            10
        )

        self.get_logger().info(f'Scan Cleaner started')
        self.get_logger().info(f'  Input: {input_topic}')
        self.get_logger().info(f'  Output: {output_topic}')
        self.get_logger().info(f'  Range filter: {self.min_range}m - {self.max_range}m')

        self.filtered_count = 0
        self.total_count = 0

    def scan_callback(self, msg):
        """Filter scan data and publish cleaned version"""
        # Copy the message
        filtered_scan = LaserScan()
        filtered_scan.header = msg.header
        filtered_scan.angle_min = msg.angle_min
        filtered_scan.angle_max = msg.angle_max
        filtered_scan.angle_increment = msg.angle_increment
        filtered_scan.time_increment = msg.time_increment
        filtered_scan.scan_time = msg.scan_time
        filtered_scan.range_min = self.min_range  # Update min range
        filtered_scan.range_max = self.max_range

        # Filter ranges
        filtered_ranges = []
        for r in msg.ranges:
            self.total_count += 1

            # Replace invalid readings with infinity
            if math.isnan(r) or math.isinf(r):
                filtered_ranges.append(float('inf'))
            elif r < self.min_range or r > self.max_range:
                filtered_ranges.append(float('inf'))
                self.filtered_count += 1
            else:
                filtered_ranges.append(r)

        filtered_scan.ranges = filtered_ranges
        filtered_scan.intensities = msg.intensities

        # Publish
        self.publisher.publish(filtered_scan)

        # Log stats every 100 scans
        if self.total_count % (len(msg.ranges) * 100) == 0:
            pct = (self.filtered_count / self.total_count * 100) if self.total_count > 0 else 0
            self.get_logger().info(
                f'Filtered {self.filtered_count}/{self.total_count} points ({pct:.1f}%)'
            )


def main(args=None):
    rclpy.init(args=args)
    node = ScanCleaner()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
