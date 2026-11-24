#!/usr/bin/env python3
"""obstacle_avoid.py — 실습 B-3 C안: 장애물 감지 시 정지 대신 후진

기존 obstacle_stop.py 대비 변경:
  - 장애물 감지 → 즉시 정지가 아니라 일정 시간 후진
  - 후진 완료 후 정지 (teleop이 다시 제어 가능)

실행:
  ros2 run mobile_robot_nodes obstacle_avoid
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import LaserScan


class ObstacleAvoid(Node):
    """전방 ±15° 영역 0.5m 이내 장애물 감지 시 후진."""

    STOP_DISTANCE = 0.5       # 장애물 감지 거리 (m)
    FRONT_ANGLE   = math.radians(30)  # 감지 각도 범위 (±15°)
    REVERSE_SPEED = -0.15     # 후진 속도 (m/s)
    REVERSE_TIME  = 2.0       # 후진 지속 시간 (초)

    def __init__(self):
        super().__init__('obstacle_avoid')

        self._cmd_pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)

        scan_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
        )
        self.create_subscription(LaserScan, '/scan', self._scan_cb, scan_qos)

        self._reversing = False
        self._reverse_timer = None

        self.get_logger().info(
            f'장애물 회피 노드 시작 '
            f'(감지거리={self.STOP_DISTANCE}m, 후진속도={self.REVERSE_SPEED}m/s, '
            f'후진시간={self.REVERSE_TIME}s)'
        )

    def _scan_cb(self, msg: LaserScan) -> None:
        if self._reversing or msg.angle_increment == 0.0:
            return

        center_idx = int(round((0.0 - msg.angle_min) / msg.angle_increment))
        half_count = int(round((self.FRONT_ANGLE / 2.0) / abs(msg.angle_increment)))
        n = len(msg.ranges)

        front = [
            r for r in msg.ranges[max(0, center_idx - half_count):min(n, center_idx + half_count + 1)]
            if msg.range_min < r < msg.range_max and math.isfinite(r)
        ]

        if not front:
            return

        min_d = min(front)
        if min_d < self.STOP_DISTANCE:
            self.get_logger().warn(f'⚠️ 전방 {min_d:.2f}m 장애물 감지! → 후진 시작')
            self._start_reverse()

    def _publish(self, linear_x: float) -> None:
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.twist.linear.x = float(linear_x)
        self._cmd_pub.publish(msg)

    def _start_reverse(self) -> None:
        self._reversing = True
        self._publish(self.REVERSE_SPEED)

        if self._reverse_timer is not None:
            self._reverse_timer.cancel()

        self._reverse_timer = self.create_timer(self.REVERSE_TIME, self._stop_reverse)

    def _stop_reverse(self) -> None:
        self._reverse_timer.cancel()
        self._reverse_timer = None
        self._publish(0.0)
        self._reversing = False
        self.get_logger().info('✅ 후진 완료 → 정지. teleop으로 재조작 가능')


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoid()
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
