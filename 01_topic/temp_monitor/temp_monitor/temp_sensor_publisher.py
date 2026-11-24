import rclpy
from rclpy.node import Node         #노드에 관한 얘기
from std_msgs.msg import Float64    # 데이터 형식(메시지 타입) 지정
import random                       
import math


class TempSensorPublisher(Node): #클라이언트 라이브러리에 노드를 상속시킨다.
    """
    온도 센서 시뮬레이터 노드 (Publisher)
    - /temperature 토픽으로 현실적인 온도 데이터를 1초 주기로 발행합니다.
    - 온도 시뮬레이션 공식: base_temp + 정현파 + 랜덤 노이즈
    """

    def __init__(self):
        super().__init__('temp_sensor_publisher') # super -> 상속한 부모클래스(Node라는 부모에 모든 기능들이 있음(declare등))에 해당, 이것의 초기함수를 호출함 / 로스 통신상의 노드 이름을 적어줌

        # --- 파라미터 선언 ---

        #self: 멤버변수
        #이 코드는 파라미터를 선언하여 상수,실수,문자 등으로 초기화 하는 내용
        self.declare_parameter('publish_period', 1.0)       # 발행 주기 (초)
        self.declare_parameter('base_temperature', 25.0)    # 기본 온도 (°C)
        self.declare_parameter('noise_amplitude', 0.5)      # 랜덤 노이즈 크기
        self.declare_parameter('wave_amplitude', 3.0)       # 정현파 진폭 -> sin에 곱하는 값
        self.declare_parameter('topic_name', 'temperature') # 토픽 이름

        # 파라미터 값 읽기
        # 위에서 초기화 한 내용의 값을 읽어서 멤버,일반변수에 저장함
        period = self.get_parameter('publish_period').value
        self.base_temp = self.get_parameter('base_temperature').value
        self.noise_amp = self.get_parameter('noise_amplitude').value
        self.wave_amp = self.get_parameter('wave_amplitude').value
        topic = self.get_parameter('topic_name').value

        # --- Publisher 생성 ---
        self.publisher_ = self.create_publisher(
            msg_type=Float64, #통신할때 주고 받는 메시지 형식 지정
            topic=topic,     # 메시지마다 토픽네임이 부여됨 이걸 위에서 지정한 temperature로 지정
            qos_profile=10  # 큐 사이즈 통신의 서비스 품질을 제어하기 위해 사용하는 인자 -> 버퍼의 크기 설정
        )

        # --- 타이머 생성 (주기적 콜백 호출) ---
        self.timer = self.create_timer(period, self.timer_callback) #실제로 우리가 온도를 측정하는게 아니므로 주기적으로 온도를 생성해주어야함  -> 타이머 콜백함수 호출

        # 내부 상태 변수
        self.elapsed_time = 0.0   # 노드 시작 후 경과 시간 (초)
        self.publish_count = 0    # 누적 발행 횟수

        self.get_logger().info(
            f'[TempSensorPublisher] 시작\n'
            f'  - 토픽        : /{topic}\n'
            f'  - 발행 주기   : {period} 초\n'
            f'  - 기본 온도   : {self.base_temp} degC'
        )

    def simulate_temperature(self) -> float:
        """
        현실적인 온도 데이터 시뮬레이션
        공식: temperature = base_temp + wave_amp*sin(2*pi*t/30) + noise
          - wave: 30초 주기 정현파 (완만한 온도 변화 모델링)
          - noise: 균등 분포 랜덤 노이즈 (센서 측정 오차 모델링)
        """
        wave = self.wave_amp * math.sin(2 * math.pi * self.elapsed_time / 30.0) # 2*파이*30 -> 30번 반복했을 떄 한 주기가 되는 -3~3까지의 값을 가지는 사인함수
        noise = random.uniform(-self.noise_amp, self.noise_amp)   #랜덤함수를 통해 노이즈 생성/uniform: 일정한 범위에서 같은 확률로 발생할수 있게 지정/noise_amp를 0.5로 지정해놨으므로 -0.5~0.5사이의 값을 가짐
        return self.base_temp + wave + noise # base_temp:베이스 시작 온도, 25도로 위에서 초기화 해놨으므로 25에서 -3~3까지의 값 즉 22에서 28까지의 온도를 생성

    def timer_callback(self):
        """타이머 콜백: 주기마다 온도 데이터를 생성하고 발행합니다."""
        self.elapsed_time += 1.0 #1씩 증가하면서 시간경과를 표현함
        self.publish_count += 1  # 

        # 온도 시뮬레이션 후 메시지 생성 및 발행
        temperature = self.simulate_temperature() #온도를 측정한 값을 할당
        msg = Float64()                          # 토픽메시지의 메시지 타입 지정
        msg.data = round(temperature, 2)         # 멤버변수에 실제 데이터를 소수점 둘째자리에서 반올림 해서 저장
        self.publisher_.publish(msg)             

        self.get_logger().info(
            f'[Published #{self.publish_count:04d}] Temperature: {msg.data:6.2f} degC' #보낸 정보 화면에 출력
        )


def main(args=None): # 이 내용정도는 계속 쓰이므로 암기해두는게 좋음
    rclpy.init(args=args)
    node = TempSensorPublisher()
    try:
        rclpy.spin(node)                  #  정상실행 spin -> 이벤트가 발생했는지 계속 체크하는 형식, 이벤트를 위해 노드를 넣음  (while문은 많은 메모리를 먹다가 다운될 수 있음)
    except KeyboardInterrupt:
        node.get_logger().info('키보드 인터럽트 - 노드를 종료합니다.') #에러가 났을 시 -> 키보드 인터럽트로 우리가 눌렀을 때 info -> 화면에 출력함 + 로그기록이 남게됨
    finally:                        # 마지막에 끝나고 아래 명령어 실행 
        node.destroy_node()         # 메모리의 인스턴스를 동적으로 할당한 것이므로 제거해둬야 함 즉, 메모리해제
        rclpy.shutdown()            # 로스 클라이언트 라이브러리를 종료


if __name__ == '__main__':
    main()
