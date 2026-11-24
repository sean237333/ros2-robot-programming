import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32


class CounterPublisher(Node):
    """
    카운터 Publisher 노드
    - /counter 토픽으로 0부터 1씩 증가하는 정수를 발행합니다.
    - 카운터가 10의 배수일 때 로그 레벨을 warn으로 출력합니다.
    """

    def __init__(self):
        super().__init__('counter_publisher')

        # 파라미터 선언
        self.declare_parameter('publish_period', 0.5)  # 발행 주기(초)

        # 파라미터 값 읽기
        period = self.get_parameter('publish_period').value

        # Publisher 생성
        self.publisher_ = self.create_publisher(
            msg_type=Int32,
            topic='/counter',
            qos_profile=10
        )

        # --- 타이머 생성 ---
        self.timer = self.create_timer(period, self.timer_callback)

        # 카운터 초기값
        self.count = 0

        self.get_logger().info(
            f'[CounterPublisher] 시작\n'
            f'  - 토픽      : /counter\n'
            f'  - 발행 주기 : {period} 초'
        )

    def timer_callback(self):
        """타이머 콜백: 카운터 값을 발행하고 1 증가시킵니다."""
        msg = Int32()
        msg.data = self.count
        self.publisher_.publish(msg)

        log_msg = f'[Published] count= {self.count}'
        if self.count % 10 == 0:
            self.get_logger().warn(log_msg)
        else:
            self.get_logger().info(log_msg)

        self.count += 1


def main(args=None):
    rclpy.init(args=args)
    node = CounterPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('키보드 인터럽트 - 노드를 종료합니다.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
