#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
ROS1/ROS2 bridge smoke test

1. Terminal A: start ROS1 master
   source /opt/ros/noetic/setup.bash
   roscore

2. Terminal B: start bridge
   export ROS1_SETUP_BASH=/opt/ros/noetic/setup.bash
   export ROS2_SETUP_BASH=/opt/ros/humble/setup.bash
   ./scripts/run_ros1_bridge.sh

3. Terminal C: ROS1 -> ROS2 test
   source /opt/ros/noetic/setup.bash
   rostopic pub /bridge_smoke std_msgs/String "data: 'hello from ros1'" -r 1

4. Terminal D: verify on ROS2
   source /opt/ros/humble/setup.bash
   ros2 topic echo /bridge_smoke std_msgs/msg/String

5. Terminal E: ROS2 -> ROS1 test
   source /opt/ros/humble/setup.bash
   ros2 topic pub /bridge_smoke_back std_msgs/msg/String "{data: hello_from_ros2}" -r 1

6. Terminal F: verify on ROS1
   source /opt/ros/noetic/setup.bash
   rostopic echo /bridge_smoke_back

After the standard String test passes, switch to GraspGen topics.
Relevant GraspGen topics:
  ROS2 input:  /camera/camera/depth/color/points
  ROS2 input:  /yolov8_seg_node/result_cloud
  ROS2 output: /grasp/best_pose
  ROS2 output: /grasp_markers
  TF: /tf and /tf_static
EOF
