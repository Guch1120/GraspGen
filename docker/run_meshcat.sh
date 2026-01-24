#!/bin/bash
docker run \
  --gpus all \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,graphics,utility \
  --runtime nvidia \
  -e NVIDIA_DISABLE_REQUIRE=1 \
  --net host \
  graspgen:latest \
  meshcat-server
