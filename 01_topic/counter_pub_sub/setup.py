from setuptools import find_packages, setup

package_name = 'counter_pub_sub'

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
            'counter_pub = counter_pub_sub.counter_publisher:main',
            'counter_sub = counter_pub_sub.counter_subscriber:main',
        ],
    },
)
