import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64


class TempMonitorSubscriber(Node):
    """
    온도 모니터 노드 (Subscriber)
    - /temperature 토픽을 구독하여 수신된 데이터를 분석합니다.
    - 온도 수준을 정상(NORMAL) / 경고(WARNING) / 위험(CRITICAL)으로 분류합니다.
    - 최솟값/최댓값/평균을 추적하고, stats_interval 횟수마다 통계를 출력합니다.
    """

    def __init__(self):
        super().__init__('temp_monitor_subscriber') #부모 클래스에 노드이름을 저장

        # --- 파라미터 선언 ---
        self.declare_parameter('warning_threshold', 27.0)   # 경고 임계 온도 (°C)
        self.declare_parameter('critical_threshold', 29.0)  # 위험 임계 온도 (°C)
        self.declare_parameter('topic_name', 'temperature') # 구독 토픽 이름
        self.declare_parameter('stats_interval', 10)        # 통계 출력 간격 (수신 횟수)

        # 파라미터 값 읽기
        self.warn_thresh = self.get_parameter('warning_threshold').value
        self.crit_thresh = self.get_parameter('critical_threshold').value
        topic = self.get_parameter('topic_name').value
        self.stats_interval = self.get_parameter('stats_interval').value

        # --- Subscriber 생성 ---
        self.subscription = self.create_subscription(
            msg_type=Float64, # 타입이름이 같아야지 퍼블리셔와 통신가능
            topic=topic, #토픽 이름은 같아야지 퍼블리셔와 통신가능
            callback=self.listener_callback, #수신할떄 필요한 콜백함수 지정
            qos_profile=10  # 큐 사이즈
        )

        # 통계 데이터 초기화
        self.receive_count = 0           # 누적 수신 횟수
        self.temp_sum = 0.0              # 온도 합계 (평균 계산용)
        self.temp_min = float('inf')     # 최솟값
        self.temp_max = float('-inf')    # 최댓값
        self.warning_count = 0           # 경고 발생 횟수
        self.critical_count = 0          # 위험 발생 횟수

        self.get_logger().info(
            f'[TempMonitorSubscriber] 시작\n'
            f'  - 구독 토픽   : /{topic}\n'
            f'  - 경고 임계값 : {self.warn_thresh} degC\n'
            f'  - 위험 임계값 : {self.crit_thresh} degC'
        )

    def classify_temperature(self, temp: float) -> tuple[str, str]:
        """
        온도 수준을 분류합니다.
        반환값: (상태 문자열, 로그 레벨 문자열)
        """
        if temp >= self.crit_thresh:
            return '[CRITICAL]', 'critical'
        elif temp >= self.warn_thresh:
            return '[WARNING] ', 'warning'
        else:
            return '[NORMAL]  ', 'normal'

    def update_stats(self, temp: float):
        """수신된 온도로 통계 데이터를 갱신합니다."""
        self.receive_count += 1
        self.temp_sum += temp
        self.temp_min = min(self.temp_min, temp)
        self.temp_max = max(self.temp_max, temp)

    def print_stats(self):
        """누적 통계를 출력합니다."""
        avg = self.temp_sum / self.receive_count
        self.get_logger().info(
            f'\n{"="*48}\n'
            f'  온도 통계 ({self.receive_count}회 수신)\n'
            f'  - 평균 : {avg:.2f} degC\n'
            f'  - 최솟값: {self.temp_min:.2f} degC\n'
            f'  - 최댓값: {self.temp_max:.2f} degC\n'
            f'  - 경고 횟수: {self.warning_count}\n'
            f'  - 위험 횟수: {self.critical_count}\n'
            f'{"="*48}'
        )

    def listener_callback(self, msg: Float64):
        """Subscriber 콜백: 메시지 수신 시 자동으로 호출됩니다."""
        temp = msg.data
        self.update_stats(temp)  # 통계 갱신

        # 온도 분류 및 로그 레벨에 맞게 출력
        status_str, level = self.classify_temperature(temp)
        log_msg = (
            f'[Received #{self.receive_count:04d}] '
            f'{status_str} Temperature: {temp:6.2f} degC'
        )
        # get_logger: 화면에 출력,로그에 기록하는 함수이며 info, warn, error등으로 색깔의 차별화를 두어 화면에 출력함
        if level == 'critical':
            self.critical_count += 1
            self.get_logger().error(log_msg)
        elif level == 'warning':
            self.warning_count += 1
            self.get_logger().warn(log_msg)
        else:
            self.get_logger().info(log_msg)

        # stats_interval 횟수마다 통계 출력
        if self.receive_count % self.stats_interval == 0:
            self.print_stats()


def main(args=None):
    rclpy.init(args=args)
    node = TempMonitorSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('키보드 인터럽트 - 노드를 종료합니다.')
        if node.receive_count > 0:
            node.print_stats()  # 종료 전 최종 통계 출력
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
