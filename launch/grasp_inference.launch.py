from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    params_file_arg = DeclareLaunchArgument(
        'params_file',
        default_value='pram/ros_inference_advanced.yaml',
        description='ROS2 parameter file for grasp inference node'
    )

    node_cmd = ExecuteProcess(
        cmd=[
            'python3', 'scripts/ros_inference_advanced.py',
            '--ros-args',
            '--params-file', LaunchConfiguration('params_file'),
        ],
        output='screen'
    )

    return LaunchDescription([
        params_file_arg,
        node_cmd,
    ])
