from setuptools import find_packages, setup

package_name = 'mobile_robot_nodes'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sean237333',
    maintainer_email='101160576+sean237333@users.noreply.github.com',
    description='Odometry/LiDAR-based control and verification nodes for a differential-drive robot',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'spin_360 = mobile_robot_nodes.spin_360:main',
            'topic_verifier = mobile_robot_nodes.topic_verifier:main',
            'obstacle_avoid = mobile_robot_nodes.obstacle_avoid:main',
        ],
    },
)
