from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'temp_converter'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sean237333',
    maintainer_email='101160576+sean237333@users.noreply.github.com',
    description='Temperature unit conversion service server and client nodes',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'temp_converter_server = temp_converter.temp_converter_server:main',
            'temp_converter_client = temp_converter.temp_converter_client:main',
        ],
    },
)
