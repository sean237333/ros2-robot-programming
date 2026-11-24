import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64


class DataAggregator(Node):
    """
    멀티 토픽 집계 Subscriber 노드
    - /sensor/temperature, /sensor/humidity 두 토픽을 동시에 구독합니다.
    - 각 센서별 수신 횟수, 최솟값, 최댓값, 누적 평균을 계산합니다.
    - stats_interval 횟수마다 두 센서의 통계를 한 번에 출력합니다.
    - 온도 > 30°C 이면 '고온 경고', 습도 > 70% 이면 '고습 경고' 출력합니다.
    """

    TEMP_WARN_THRESHOLD = 30.0   # 고온 경고 임계값 (°C)
    HUMI_WARN_THRESHOLD = 70.0   # 고습 경고 임계값 (%)

    def __init__(self):
        super().__init__('data_aggregator')

        # --- 파라미터 선언 ---
        self.declare_parameter('stats_interval', 5)  # 통계 출력 간격 (수신 횟수)

        self.stats_interval = self.get_parameter('stats_interval').value

        # --- Subscriber 생성 (온도, 습도 각각 독립 콜백) ---
        self.temp_sub = self.create_subscription(
            msg_type=Float64,
            topic='sensor/temperature',
            callback=self.temp_callback,
            qos_profile=10
        )
        self.humi_sub = self.create_subscription(
            msg_type=Float64,
            topic='sensor/humidity',
            callback=self.humi_callback,
            qos_profile=10
        )

        # 온도 통계 변수 초기화
        self.temp_count = 0
        self.temp_sum = 0.0
        self.temp_min = float('inf')
        self.temp_max = float('-inf')

        # 습도 통계 변수 초기화
        self.humi_count = 0
        self.humi_sum = 0.0
        self.humi_min = float('inf')
        self.humi_max = float('-inf')

        self.last_printed = 0  # 마지막으로 통계를 출력한 interval 번호

        self.get_logger().info(
            f'[DataAggregator] 시작 — 통계 출력 간격: {self.stats_interval}회'
        )

    # 통계 갱신 헬퍼

    def _update_temp_stats(self, value: float):
        self.temp_count += 1
        self.temp_sum += value
        self.temp_min = min(self.temp_min, value)
        self.temp_max = max(self.temp_max, value)

    def _update_humi_stats(self, value: float):
        self.humi_count += 1
        self.humi_sum += value
        self.humi_min = min(self.humi_min, value)
        self.humi_max = max(self.humi_max, value)

    # 통계 출력

    def _try_print_stats(self):
        """온도·습도 둘 다 interval에 도달했을 때만 통계를 출력합니다."""
        current = min(self.temp_count, self.humi_count)
        target = (current // self.stats_interval) * self.stats_interval
        if target > 0 and target > self.last_printed:
            self.last_printed = target
            self._print_stats()

    def _print_stats(self):
        temp_avg = self.temp_sum / self.temp_count if self.temp_count else 0.0
        humi_avg = self.humi_sum / self.humi_count if self.humi_count else 0.0
        self.get_logger().info(
            f'\n{"="*50}\n'
            f'  [통계] 온도 (수신 {self.temp_count}회)\n'
            f'    평균: {temp_avg:.2f}°C  '
            f'최솟값: {self.temp_min:.2f}°C  '
            f'최댓값: {self.temp_max:.2f}°C\n'
            f'  [통계] 습도 (수신 {self.humi_count}회)\n'
            f'    평균: {humi_avg:.2f}%   '
            f'최솟값: {self.humi_min:.2f}%   '
            f'최댓값: {self.humi_max:.2f}%\n'
            f'{"="*50}'
        )

    # 콜백 함수

    def temp_callback(self, msg: Float64):
        """온도 토픽 수신 콜백"""
        temp = msg.data
        self._update_temp_stats(temp)

        self.get_logger().info(
            f'[TEMP] {temp:.2f}°C  (수신 #{self.temp_count})'
        )

        # 고온 경고
        if temp > self.TEMP_WARN_THRESHOLD:
            self.get_logger().warn(
                f'[TEMP] 고온 경고! {temp:.2f}°C > {self.TEMP_WARN_THRESHOLD}°C'
            )

        self._try_print_stats()

    def humi_callback(self, msg: Float64):
        """습도 토픽 수신 콜백"""
        humi = msg.data
        self._update_humi_stats(humi)

        self.get_logger().info(
            f'[HUMI] {humi:.2f}%   (수신 #{self.humi_count})'
        )

        # 고습 경고
        if humi > self.HUMI_WARN_THRESHOLD:
            self.get_logger().warn(
                f'[HUMI] 고습 경고! {humi:.2f}% > {self.HUMI_WARN_THRESHOLD}%'
            )

        self._try_print_stats()


def main(args=None):
    rclpy.init(args=args)
    node = DataAggregator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('키보드 인터럽트 - 노드를 종료합니다.')
        if node.temp_count > 0 or node.humi_count > 0:
            node._print_stats()  # 종료 전 최종 통계 출력
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
