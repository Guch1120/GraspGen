#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${ROS1_SETUP_BASH:-}" ]]; then
  echo "ROS1_SETUP_BASH is required. Example: /opt/ros/noetic/setup.bash" >&2
  exit 1
fi

if [[ -z "${ROS2_SETUP_BASH:-}" ]]; then
  echo "ROS2_SETUP_BASH is required. Example: /opt/ros/humble/setup.bash" >&2
  exit 1
fi

if [[ ! -f "${ROS1_SETUP_BASH}" ]]; then
  echo "ROS1 setup file not found: ${ROS1_SETUP_BASH}" >&2
  exit 1
fi

if [[ ! -f "${ROS2_SETUP_BASH}" ]]; then
  echo "ROS2 setup file not found: ${ROS2_SETUP_BASH}" >&2
  exit 1
fi

source "${ROS1_SETUP_BASH}"
if [[ -n "${ROS1_WS_SETUP_BASH:-}" ]]; then
  echo "Sourcing ROS1 workspace setup: ${ROS1_WS_SETUP_BASH}"
  source "${ROS1_WS_SETUP_BASH}"
fi

source "${ROS2_SETUP_BASH}"
if [[ -n "${ROS2_WS_SETUP_BASH:-}" ]]; then
  echo "Sourcing ROS2 workspace setup: ${ROS2_WS_SETUP_BASH}"
  source "${ROS2_WS_SETUP_BASH}"
fi

echo "Starting ros1_bridge dynamic_bridge"
echo "ROS_MASTER_URI=${ROS_MASTER_URI:-unset}"
echo "ROS_IP=${ROS_IP:-unset}"
echo "ROS_HOSTNAME=${ROS_HOSTNAME:-unset}"

exec ros2 run ros1_bridge dynamic_bridge --bridge-all-topics
