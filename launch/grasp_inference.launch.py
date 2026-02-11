from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    scene_topic_arg = DeclareLaunchArgument(
        'scene_topic', 
        default_value='/camera/camera/depth/color/points',
        description='Topic name for scene point cloud'
    )
    object_topic_arg = DeclareLaunchArgument(
        'object_topic', 
        default_value='/yolov8_seg_node/result_cloud',
        description='Topic name for object point cloud'
    )
    gripper_config_arg = DeclareLaunchArgument(
        'gripper_config', 
        default_value='GraspGenModels/checkpoints/graspgen_robotiq_2f_140.yml',
        description='Path to gripper configuration file'
    )

    # Execute the python script directly using ExecuteProcess
    # This avoids the need to install the package or define entry points in setup.py
    node_cmd = ExecuteProcess(
        cmd=[
            'python3', 'scripts/ros_inference_advanced.py',
            '--ros-args',
            '-p', ['scene_topic:=', LaunchConfiguration('scene_topic')],
            '-p', ['object_topic:=', LaunchConfiguration('object_topic')],
            '-p', ['gripper_config:=', LaunchConfiguration('gripper_config')]
        ],
        output='screen'
    )

    return LaunchDescription([
        scene_topic_arg,
        object_topic_arg,
        gripper_config_arg,
        node_cmd
    ])
