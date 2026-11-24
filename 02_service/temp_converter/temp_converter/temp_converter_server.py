import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor, ParameterType, SetParametersResult
from temp_converter_interfaces.srv import TempConvert


class TempConverterServer(Node):
    """
    온도 단위 변환 서비스 서버 노드
    - /convert_temperature 서비스로 섭씨(C) ↔ 화씨(F) 변환을 제공합니다.
    - decimal_places : 변환 결과의 소수점 자리수 (1~6).
                       실행 중 ros2 param set 으로 동적 변경이 가능합니다.
    - service_name   : 서비스 토픽 이름. 서비스 재생성이 필요하므로 동적 변경을 허용하지 않습니다.
    - 변환 공식:
        섭씨 → 화씨 : F = C × 9/5 + 32
        화씨 → 섭씨 : C = (F − 32) × 5/9
    """

    def __init__(self):
        super().__init__('temp_converter_server')

        # --- 파라미터 선언 (descriptor 로 타입·설명 명시) ---
        self.declare_parameter(
            'decimal_places', 2,
            ParameterDescriptor(
                type=ParameterType.PARAMETER_INTEGER,
                description='Number of decimal places for converted temperature (1-6). Changeable at runtime.'
            )
        )
        self.declare_parameter(
            'service_name', 'convert_temperature',
            ParameterDescriptor(
                type=ParameterType.PARAMETER_STRING,
                description='Service topic name. Node restart required to change.',
                read_only=True   # 런타임 변경 불허
            )
        )

        # 초기값 읽기
        self.decimal_places = self.get_parameter('decimal_places').value
        service_name        = self.get_parameter('service_name').value

        # --- 서비스 서버 생성 ---
        self._srv = self.create_service(
            TempConvert,
            f'/{service_name}',
            self._convert_callback
        )

        # --- 런타임 파라미터 변경 콜백 등록 ---
        self.add_on_set_parameters_callback(self._on_set_parameters)

        self.get_logger().info(
            f'[TempConverterServer] Started\n'
            f'  - Service       : /{service_name}\n'
            f'  - Decimal places: {self.decimal_places}\n'
            f'  * Use "ros2 param set /temp_converter_server <param> <value>" to change at runtime'
        )

    # ------------------------------------------------------------------
    # 런타임 파라미터 변경 콜백
    # ------------------------------------------------------------------
    def _on_set_parameters(self, params) -> SetParametersResult:
        """
        ros2 param set 호출 시 실행됩니다.
        - decimal_places 는 1~6 범위만 허용합니다.
        - 검증 통과 시 내부 상태에 즉시 반영합니다.
        """
        for param in params:
            if param.name == 'decimal_places':
                # 범위 검증: 1 이상 6 이하만 허용
                if not (1 <= param.value <= 6):
                    return SetParametersResult(
                        successful=False,
                        reason='decimal_places must be between 1 and 6'
                    )
                self.decimal_places = param.value
                self.get_logger().info(
                    f'[Param changed] decimal_places -> {param.value}'
                )

        return SetParametersResult(successful=True)

    # ------------------------------------------------------------------
    # 서비스 콜백
    # ------------------------------------------------------------------
    def _convert_callback(self, request, response) -> TempConvert.Response:
        """
        클라이언트 요청을 처리합니다.
        요청: temperature (float64), unit (string - "C" 또는 "F")
        응답: converted, result_unit, success, message
        """
        unit = request.unit.upper()   # 대소문자 구분 없이 처리

        if unit == 'C':
            # 섭씨 → 화씨: F = C × 9/5 + 32
            converted = request.temperature * 9.0 / 5.0 + 32.0
            response.converted    = round(converted, self.decimal_places)
            response.result_unit  = 'F'
            response.success      = True
            response.message      = (
                f'Converted {round(request.temperature, self.decimal_places)} C '
                f'to {response.converted} F'
            )
            self.get_logger().info(f'[Converted] {response.message}')

        elif unit == 'F':
            # 화씨 → 섭씨: C = (F - 32) × 5/9
            converted = (request.temperature - 32.0) * 5.0 / 9.0
            response.converted    = round(converted, self.decimal_places)
            response.result_unit  = 'C'
            response.success      = True
            response.message      = (
                f'Converted {round(request.temperature, self.decimal_places)} F '
                f'to {response.converted} C'
            )
            self.get_logger().info(f'[Converted] {response.message}')

        else:
            # 지원하지 않는 단위 → 실패 응답
            response.converted   = 0.0
            response.result_unit = ''
            response.success     = False
            response.message     = (
                f'Invalid unit "{request.unit}". Must be "C" (Celsius) or "F" (Fahrenheit).'
            )
            self.get_logger().warn(f'[Invalid request] {response.message}')

        return response


def main(args=None):
    rclpy.init(args=args)
    node = TempConverterServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard interrupt - shutting down node.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
