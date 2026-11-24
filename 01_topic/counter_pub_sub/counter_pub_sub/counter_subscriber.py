import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32


class CounterSubscriber(Node):
    """
    카운터 Subscriber 노드
    - /counter 토픽을 구독하여 수신된 값을 출력합니다.
    - 수신한 카운터 값의 짝수/홀수를 판별하여 함께 표시합니다.
    - 카운터가 milestone_interval의 배수이면 '** 이정표 도달 **' 메시지를 추가 출력합니다.
    """

    def __init__(self):
        super().__init__('counter_subscriber')

        # --- 파라미터 선언 ---
        self.declare_parameter('milestone_interval', 10)  # 이정표 출력 간격

        # 파라미터 값 읽기
        self.milestone_interval = self.get_parameter('milestone_interval').value

        # --- Subscriber 생성 ---
        self.subscription = self.create_subscription(
            msg_type=Int32,
            topic='/counter',
            callback=self.listener_callback,
            qos_profile=10
        )

        self.get_logger().info(
            f'[CounterSubscriber] 시작\n'
            f'  - 구독 토픽      : /counter\n'
            f'  - 이정표 간격    : {self.milestone_interval}'
        )

    def listener_callback(self, msg: Int32):
        """Subscriber 콜백: 메시지 수신 시 자동으로 호출됩니다."""
        number = msg.data
        parity = '짝수' if number % 2 == 0 else '홀수'

        self.get_logger().info(f'[Received] count= {number} ({parity})')

        if number % self.milestone_interval == 0:
            self.get_logger().warn(f'** 이정표 도달 ** count={number}')


def main(args=None):
    rclpy.init(args=args)
    node = CounterSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('키보드 인터럽트 - 노드를 종료합니다.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
