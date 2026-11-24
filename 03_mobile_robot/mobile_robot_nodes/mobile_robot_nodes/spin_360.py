#!/usr/bin/env python3
"""spin_360.py — 실습 A-3: odom 피드백으로 정확히 360° 회전 후 자동 정지

실행:
  ros2 run mobile_robot_nodes spin_360
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry


def quat_to_yaw(q) -> float:
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def normalize_angle(a: float) -> float:
    """각도를 [-π, π] 범위로 정규화."""
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


class Spin360(Node):
    """odom 피드백 기반 정확한 360° 회전."""

    TARGET = 2.0 * math.pi        # 360°
    ANGULAR_SPEED = 0.3           # rad/s (느릴수록 정확)
    TOLERANCE = 0.01              # rad (≈ 0.57°)

    def __init__(self):
        super().__init__('spin_360')

        self._cmd_pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self._odom_sub = self.create_subscription(
            Odometry, '/odom', self._odom_cb, 10
        )

        self._prev_yaw: float | None = None
        self._accumulated: float = 0.0
        self._done: bool = False

        self.get_logger().info(
            f'360° 회전 시작 (속도={self.ANGULAR_SPEED} rad/s) — odom 피드백 사용'
        )

    def _odom_cb(self, msg: Odometry) -> None:
        if self._done:
            return

        yaw = quat_to_yaw(msg.pose.pose.orientation)

        if self._prev_yaw is None:
            self._prev_yaw = yaw
            self.get_logger().info(f'시작 yaw: {math.degrees(yaw):.2f}°')
            return

        delta = normalize_angle(yaw - self._prev_yaw)
        self._accumulated += abs(delta)
        self._prev_yaw = yaw

        remaining = self.TARGET - self._accumulated

        if remaining <= self.TOLERANCE:
            self._stop()
            return

        # 부드러운 감속: 남은 각도가 작으면 속도 줄이기
        speed = self.ANGULAR_SPEED
        if remaining < 0.3:
            speed = max(0.1, self.ANGULAR_SPEED * (remaining / 0.3))

        self._publish(speed)
        self.get_logger().info(
            f'회전: {math.degrees(self._accumulated):.1f}° / 360°'
            f'  (남은 {math.degrees(remaining):.1f}°)',
            throttle_duration_sec=0.5,
        )

    def _publish(self, angular_z: float) -> None:
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.twist.angular.z = float(angular_z)
        self._cmd_pub.publish(msg)

    def _stop(self) -> None:
        self._done = True
        self._publish(0.0)
        self.get_logger().info(
            f'✅ 완료! 총 회전: {math.degrees(self._accumulated):.2f}°'
        )


def main(args=None):
    rclpy.init(args=args)
    node = Spin360()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._publish(0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
