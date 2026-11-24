"""
temp_converter_launch.py
========================
서버 노드(temp_converter_server) + 클라이언트 노드(temp_converter_client)를
함께 실행하는 런치 파일입니다.

사용법 (기본 - request_period=2.0 초):
    ros2 launch temp_converter temp_converter_launch.py

사용법 (request_period 변경):
    ros2 launch temp_converter temp_converter_launch.py request_period:=0.5

런치 인자:
    request_period  (float, 기본값 2.0)  - 클라이언트 서비스 요청 주기(초)
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('temp_converter')

    # YAML 파라미터 파일 경로
    server_params = os.path.join(pkg_share, 'config', 'server_params.yaml')
    client_params = os.path.join(pkg_share, 'config', 'client_params.yaml')

    # --- 런치 인자 선언 ---
    declare_request_period = DeclareLaunchArgument(
        name='request_period',
        default_value='2.0',
        description='클라이언트 서비스 요청 주기 (초)'
    )

    request_period = LaunchConfiguration('request_period')

    # --- 서버 노드 ---
    server_node = Node(
        package='temp_converter',
        executable='temp_converter_server',
        name='temp_converter_server',
        output='screen',
        # 서버 전용 YAML 파라미터 파일 로드
        parameters=[server_params],
    )

    # --- 클라이언트 노드 ---
    client_node = Node(
        package='temp_converter',
        executable='temp_converter_client',
        name='temp_converter_client',
        output='screen',
        parameters=[
            # 클라이언트 전용 YAML 파라미터 파일 로드
            client_params,
            # 런치 인자로 받은 request_period 로 YAML 기본값을 덮어씀
            {'request_period': request_period},
        ],
    )

    return LaunchDescription([
        declare_request_period,
        server_node,
        client_node,
    ])
