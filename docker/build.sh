VER=1.0
MODE="${1:-ros2}"

case "$MODE" in
  ros1)
    DOCKERFILE="docker/graspgen_cuda121_ros1.dockerfile"
    IMAGE_NAME="graspgen:ros1"
    ;;
  ros2)
    DOCKERFILE="docker/graspgen_cuda121_ros2.dockerfile"
    IMAGE_NAME="graspgen:ros2"
    ;;
  *)
    echo "Usage: $0 [ros1|ros2]" >&2
    exit 1
    ;;
esac

docker build \
  -f "$DOCKERFILE" \
  --progress=plain \
  . \
  --network=host \
  --build-arg CURL_INSECURE="${CURL_INSECURE:-0}" \
  -t "$IMAGE_NAME"

if [ "$MODE" = "ros2" ]; then
  docker tag "$IMAGE_NAME" graspgen:$VER
  docker tag "$IMAGE_NAME" graspgen:latest
fi
