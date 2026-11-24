import random

import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor, ParameterType, SetParametersResult
from temp_converter_interfaces.srv import TempConvert


class TempConverterClient(Node):
    """
    온도 단위 변환 서비스 클라이언트 노드
    - request_period 주기마다 타이머가 발동하여 서비스 요청을 보냅니다.
    - 요청 온도는 [input_temp_min, input_temp_max] 범위에서 무작위로 생성됩니다.
    - 응답은 call_async() + add_done_callback() 비동기 패턴으로 처리합니다.
    - request_period     : 서비스 요청 주기(초). 변경 시 타이머를 재생성합니다.
    - input_temp_min     : 랜덤 온도 범위 최솟값. 실행 중 동적 변경이 가능합니다.
    - input_temp_max     : 랜덤 온도 범위 최댓값. 실행 중 동적 변경이 가능합니다.
    - target_unit        : 요청 단위 ("C" 또는 "F"). 실행 중 동적 변경이 가능합니다.
    - input_temp_min < input_temp_max 조건을 항상 유지합니다.
    """

    def __init__(self):
        super().__init__('temp_converter_client')

        # --- 파라미터 선언 (descriptor 로 타입·설명 명시) ---
        self.declare_parameter(
            'request_period', 2.0,
            ParameterDescriptor(
                type=ParameterType.PARAMETER_DOUBLE,
                description='Period (sec) between service requests. Timer is recreated when changed at runtime.'
            )
        )
        self.declare_parameter(
            'input_temp_min', -20.0,
            ParameterDescriptor(
                type=ParameterType.PARAMETER_DOUBLE,
                description='Minimum value of randomly generated input temperature. Changeable at runtime.'
            )
        )
        self.declare_parameter(
            'input_temp_max', 100.0,
            ParameterDescriptor(
                type=ParameterType.PARAMETER_DOUBLE,
                description='Maximum value of randomly generated input temperature. Changeable at runtime.'
            )
        )
        self.declare_parameter(
            'target_unit', 'C',
            ParameterDescriptor(
                type=ParameterType.PARAMETER_STRING,
                description='Input temperature unit to send: "C" (Celsius) or "F" (Fahrenheit). Changeable at runtime.'
            )
        )

        # 초기값 읽기
        self._period    = self.get_parameter('request_period').value
        self.temp_min   = self.get_parameter('input_temp_min').value
        self.temp_max   = self.get_parameter('input_temp_max').value
        self.target_unit = self.get_parameter('target_unit').value

        # --- 서비스 클라이언트 생성 ---
        self._client = self.create_client(TempConvert, '/convert_temperature')

        # 서버가 준비될 때까지 1초 간격으로 대기
        while not self._client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /convert_temperature service...')

        # --- 타이머 생성 ---
        self.timer = self.create_timer(self._period, self.timer_callback)

        # 요청 카운터
        self.request_count = 0

        # --- 런타임 파라미터 변경 콜백 등록 ---
        self.add_on_set_parameters_callback(self._on_set_parameters)

        self.get_logger().info(
            f'[TempConverterClient] Started\n'
            f'  - Service       : /convert_temperature\n'
            f'  - Request period: {self._period} sec\n'
            f'  - Temp range    : [{self.temp_min}, {self.temp_max}]\n'
            f'  - Target unit   : {self.target_unit}\n'
            f'  * Use "ros2 param set /temp_converter_client <param> <value>" to change at runtime'
        )

    # ------------------------------------------------------------------
    # 런타임 파라미터 변경 콜백
    # ------------------------------------------------------------------
    def _on_set_parameters(self, params) -> SetParametersResult:
        """
        ros2 param set 호출 시 실행됩니다.
        - input_temp_min < input_temp_max 교차 검증을 수행합니다.
        - request_period 변경 시 타이머를 재생성합니다.
        - 검증 통과 시 내부 상태에 즉시 반영합니다.
        """
        # 변경 후 min/max 값을 미리 계산 (교차 검증용)
        new_min = self.temp_min
        new_max = self.temp_max

        for param in params:
            if param.name == 'input_temp_min':
                new_min = param.value
            elif param.name == 'input_temp_max':
                new_max = param.value

        # 교차 검증: 최솟값이 최댓값보다 크거나 같으면 거부
        if new_min >= new_max:
            return SetParametersResult(
                successful=False,
                reason=(
                    f'input_temp_min({new_min}) must be less than '
                    f'input_temp_max({new_max})'
                )
            )

        # 검증 통과 → 내부 상태 반영
        need_timer_reset = False

        for param in params:
            if param.name == 'request_period':
                # 발행 주기는 양수여야 함
                if param.value <= 0.0:
                    return SetParametersResult(
                        successful=False,
                        reason='request_period must be > 0.0'
                    )
                self._period     = param.value
                need_timer_reset = True
                self.get_logger().info(
                    f'[Param changed] request_period -> {param.value} sec  (timer recreated)'
                )

            elif param.name == 'input_temp_min':
                self.temp_min = param.value
                self.get_logger().info(
                    f'[Param changed] input_temp_min -> {param.value}'
                )

            elif param.name == 'input_temp_max':
                self.temp_max = param.value
                self.get_logger().info(
                    f'[Param changed] input_temp_max -> {param.value}'
                )

            elif param.name == 'target_unit':
                self.target_unit = param.value
                self.get_logger().info(
                    f'[Param changed] target_unit -> {param.value}'
                )

        # request_period 변경 시 타이머 재생성
        if need_timer_reset:
            self.timer.cancel()
            self.timer = self.create_timer(self._period, self.timer_callback)

        return SetParametersResult(successful=True)

    # ------------------------------------------------------------------
    # 타이머 콜백 · 응답 콜백
    # ------------------------------------------------------------------
    def timer_callback(self):
        """타이머 콜백: 주기마다 랜덤 온도를 생성하여 서비스에 비동기 요청을 보냅니다."""
        self.request_count += 1

        # [temp_min, temp_max] 범위의 랜덤 온도 생성 (소수점 2자리)
        temperature = round(random.uniform(self.temp_min, self.temp_max), 2)

        request = TempConvert.Request()
        request.temperature = temperature
        request.unit        = self.target_unit

        # 비동기 호출: 응답이 도착하면 _response_callback 이 자동 호출됨
        future = self._client.call_async(request)
        future.add_done_callback(self._response_callback)

        self.get_logger().info(
            f'[Request #{self.request_count:04d}] {temperature} {self.target_unit}'
        )

    def _response_callback(self, future):
        """서비스 응답 처리 콜백: call_async() 의 Future 가 완료되면 호출됩니다."""
        try:
            response = future.result()
            if response.success:
                self.get_logger().info(
                    f'[Response] {response.message}'
                )
            else:
                self.get_logger().warn(
                    f'[Response] Conversion failed: {response.message}'
                )
        except Exception as e:
            self.get_logger().error(f'[Response] Service call failed: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = TempConverterClient()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard interrupt - shutting down node.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
