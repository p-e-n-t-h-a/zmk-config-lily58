#!/usr/bin/env bash
# Build every board/shield combination listed in build.yaml, using the
# zmkfirmware/zmk-build-arm Docker image. Run ./install.sh first (and again
# whenever config/west.yml changes).
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -d .west ]; then
  echo "No .west workspace found. Run ./install.sh first." >&2
  exit 1
fi

IMAGE="zmkfirmware/zmk-build-arm:stable"

# Run the container as the owner of this directory (not root), so
# everything it creates (build/, export/, ...) is owned by you, not root.
HOST_UID_GID="$(stat -c '%u:%g' "$PWD")"

docker run --rm -it \
  --user "$HOST_UID_GID" \
  -e HOME=/tmp \
  -v "$PWD:/workspace" \
  -w /workspace \
  "$IMAGE" \
  bash -euo pipefail -c '
    west zephyr-export
    python3 scripts/build_from_matrix.py
  '
