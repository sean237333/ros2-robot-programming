#!/usr/bin/env python3
"""topic_verifier.py — 실습 A-2: Teleop 주행과 토픽 검증

관찰표의 4개 토픽을 실시간 모니터링합니다:
  /cmd_vel  — 키 입력 시 linear.x / angular.z 변화
  /odom     — 정지 시 발행 빈도 (≈50 Hz)
  /scan     — ranges 배열 길이 (≈360)
  /tf       — odom → base_link 갱신 여부

실행:
  ros2 run mobile_robot_nodes topic_verifier
"""

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from tf2_ros import TransformListener, Buffer


_SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)


class TopicVerifier(Node):
    """실습 A-2 관찰표 실시간 출력."""

    def __init__(self):
        super().__init__('topic_verifier')

        # --- /cmd_vel ---
        self._cmd_linear_x: float = 0.0
        self._cmd_angular_z: float = 0.0
        self._cmd_count: int = 0

        # --- /odom ---
        self._odom_x: float = 0.0
        self._odom_y: float = 0.0
        self._odom_yaw: float = 0.0
        self._odom_count: int = 0
        self._odom_hz_window: list[float] = []

        # --- /scan ---
        self._scan_ranges_len: int = 0
        self._scan_count: int = 0

        # --- /tf ---
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)
        self._tf_ok: bool = False

        self.create_subscription(TwistStamped, '/cmd_vel', self._cmd_cb, 10)
        self.create_subscription(Odometry, '/odom', self._odom_cb, 10)
        self.create_subscription(LaserScan, '/scan', self._scan_cb, _SENSOR_QOS)

        self.create_timer(1.0, self._print_table)
        self.get_logger().info('토픽 검증 시작 — teleop을 실행해 로봇을 조작하세요.')

    # ------------------------------------------------------------------ #
    # Callbacks
    # ------------------------------------------------------------------ #

    def _cmd_cb(self, msg: TwistStamped) -> None:
        self._cmd_linear_x = msg.twist.linear.x
        self._cmd_angular_z = msg.twist.angular.z
        self._cmd_count += 1

    def _odom_cb(self, msg: Odometry) -> None:
        self._odom_x = msg.pose.pose.position.x
        self._odom_y = msg.pose.pose.position.y
        self._odom_yaw = self._quat_to_yaw(msg.pose.pose.orientation)
        self._odom_count += 1

        now = time.monotonic()
        self._odom_hz_window.append(now)
        cutoff = now - 1.0
        self._odom_hz_window = [t for t in self._odom_hz_window if t >= cutoff]

    def _scan_cb(self, msg: LaserScan) -> None:
        self._scan_ranges_len = len(msg.ranges)
        self._scan_count += 1

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _quat_to_yaw(q) -> float:
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def _check_tf(self) -> bool:
        try:
            self._tf_buffer.lookup_transform('odom', 'base_link', rclpy.time.Time())
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # Table print
    # ------------------------------------------------------------------ #

    def _print_table(self) -> None:
        self._tf_ok = self._check_tf()
        odom_hz = len(self._odom_hz_window)

        cmd_status = (
            f'linear.x={self._cmd_linear_x:+.2f}  angular.z={self._cmd_angular_z:+.2f}'
            f'  (수신 {self._cmd_count}회)'
        )
        odom_status = (
            f'x={self._odom_x:.3f}  y={self._odom_y:.3f}'
            f'  yaw={math.degrees(self._odom_yaw):.1f}°'
            f'  ≈{odom_hz} Hz'
        )
        scan_status = (
            f'ranges 길이={self._scan_ranges_len}'
            f'  (수신 {self._scan_count}회)'
        )
        tf_status = '✅ odom→base_link 갱신 중' if self._tf_ok else '❌ TF 없음 (Webots 미실행?)'

        sep = '─' * 60
        print(f'\n{sep}')
        print('  실습 A-2  토픽 검증 관찰표')
        print(sep)
        print(f'  /cmd_vel  │ {cmd_status}')
        print(f'  /odom     │ {odom_status}')
        print(f'  /scan     │ {scan_status}')
        print(f'  /tf       │ {tf_status}')
        print(sep)


def main(args=None):
    rclpy.init(args=args)
    node = TopicVerifier()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
