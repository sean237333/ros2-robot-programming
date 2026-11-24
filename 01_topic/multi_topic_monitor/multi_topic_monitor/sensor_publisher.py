import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
import random


class SensorPublisher(Node):
    """
    멀티 토픽 센서 Publisher 노드
    - /sensor/temperature : 온도 (20.0~35.0 degC) 랜덤 값, 1초 주기 발행
    - /sensor/humidity    : 습도 (30.0~80.0 %)    랜덤 값, 1초 주기 발행
    """

    def __init__(self):
        super().__init__('sensor_publisher')

        # --- 파라미터 선언 ---
        self.declare_parameter('publish_period', 1.0)  # 발행 주기 (초)

        period = self.get_parameter('publish_period').value

        # --- Publisher 생성 (온도, 습도 각각) ---
        self.temp_pub = self.create_publisher(
            msg_type=Float64,
            topic='sensor/temperature',
            qos_profile=10
        )
        self.humi_pub = self.create_publisher(
            msg_type=Float64,
            topic='sensor/humidity',
            qos_profile=10
        )

        # --- 타이머 생성 ---
        self.timer = self.create_timer(period, self.timer_callback)

        self.publish_count = 0  # 누적 발행 횟수

        self.get_logger().info(
            f'[SensorPublisher] 시작 — 발행 주기: {period}초'
        )

    def timer_callback(self):
        """타이머 콜백: 온도·습도 데이터를 생성하고 각 토픽으로 발행합니다."""
        self.publish_count += 1

        temp = round(random.uniform(20.0, 35.0), 2)  # 온도 랜덤 생성
        humi = round(random.uniform(30.0, 80.0), 2)  # 습도 랜덤 생성

        temp_msg = Float64()
        temp_msg.data = temp
        self.temp_pub.publish(temp_msg)

        humi_msg = Float64()
        humi_msg.data = humi
        self.humi_pub.publish(humi_msg)

        self.get_logger().info(
            f'[#{self.publish_count:04d}] Temp={temp:.2f}°C  Humi={humi:.2f}%'
        )


def main(args=None):
    rclpy.init(args=args)
    node = SensorPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('키보드 인터럽트 - 노드를 종료합니다.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
