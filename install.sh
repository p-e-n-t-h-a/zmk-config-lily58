#!/usr/bin/env bash
# One-time (or after config/west.yml changes) setup of the local West/Zephyr
# workspace, using the zmkfirmware/zmk-build-arm Docker image.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

IMAGE="zmkfirmware/zmk-build-arm:stable"

# Run the container as the owner of this directory (not root), so
# everything it creates in the bind-mounted repo (.west/, zmk/, zephyr/,
# build/, export/, ...) is owned by you, not root.
HOST_UID_GID="$(stat -c '%u:%g' "$PWD")"

echo "==> Pulling $IMAGE"
docker pull "$IMAGE"

echo "==> Initializing and updating the West workspace"
docker run --rm -it \
  --user "$HOST_UID_GID" \
  -e HOME=/tmp \
  -v "$PWD:/workspace" \
  -w /workspace \
  "$IMAGE" \
  bash -euo pipefail -c '
    if [ -d .west ]; then
      echo "West workspace already initialized, skipping west init"
    else
      west init -l config
    fi

    west update
    west zephyr-export
  '

echo "==> Setup complete. Run ./build.sh to build firmware."
