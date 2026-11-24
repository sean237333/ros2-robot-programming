from setuptools import find_packages, setup

package_name = 'temp_monitor'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sean237333',
    maintainer_email='101160576+sean237333@users.noreply.github.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'temp_sensor_pub = temp_monitor.temp_sensor_publisher:main',
            'temp_monitor_sub = temp_monitor.temp_monitor_subscriber:main',
        ],
    },
)
