# zmk-config-lily58

ZMK firmware configuration for a Lily58 (nice!nano v2, nice!view displays).

Firmware is built automatically by GitHub Actions on every push, but this
repo also supports building locally with Docker for faster iteration and to
see real compiler errors without waiting on CI.

## Prerequisites

- [Docker](https://docs.docker.com/engine/install/), running and usable by
  your user (`docker info` should succeed without `sudo`; if it doesn't,
  prefix the commands below with `sudo`)

## Setup

Run once, or again whenever `config/west.yml` changes:

```bash
./install.sh
```

This pulls the `zmkfirmware/zmk-build-arm:stable` build image and, inside a
container with the repo mounted at `/workspace`, initializes and fetches the
West workspace (`west init` + `west update` + `west zephyr-export`). Expect
the first run to take a few minutes — it pulls ZMK, Zephyr, and all module
dependencies (several hundred MB). Everything it fetches is cached on disk
under `.west/`, `zmk/`, `zephyr/`, `modules/`, etc. (via the bind mount), so
this doesn't need to be repeated for ordinary keymap/config edits.

## Build

Run every time you want to rebuild the firmware:

```bash
./build.sh
```

This builds every board/shield combination listed in [`build.yaml`](build.yaml)
— the same file GitHub Actions reads to generate its build matrix, so local
builds and CI always build the same targets. It does a pristine (`-p`, i.e.
clean) rebuild each time so Kconfig/devicetree caching can't mask config
changes. Resulting firmware is copied into `export/` (gitignored), one
`.uf2` per entry, named after its `artifact-name` (or, if that's not set,
its shield's first word, falling back to its board):

```bash
export/lily58_left.uf2
export/lily58_right.uf2
export/settings_reset.uf2
```

Flash by double-tapping reset on the target half and drag-dropping the
matching `.uf2` file onto the mass-storage device that appears.

## Notes for manual/Docker debugging

`install.sh`/`build.sh` are thin wrappers around plain `west`/Docker
commands, useful if you want to run things by hand (e.g. to get a shell
inside the build environment):

```bash
docker run --rm -it \
  --user "$(stat -c '%u:%g' "$PWD")" -e HOME=/tmp \
  -v "$PWD:/workspace" -w /workspace \
  zmkfirmware/zmk-build-arm:stable bash
```

`--user "$(stat -c '%u:%g' "$PWD")"` runs the container as the owner of the
repo directory instead of root — without it, everything the container
creates in the bind-mounted repo (`.west/`, `zmk/`, `zephyr/`, `build/`,
`export/`, ...) ends up owned by root on the host. `-e HOME=/tmp` gives that
(non-root, passwd-less) user a writable home directory inside the
container, since it doesn't persist across containers anyway.

One thing doesn't persist across containers, since it lives under `$HOME`
(`/tmp`) inside the container rather than the mounted repo, so it needs to
be redone (`install.sh`/`build.sh` already do this for you) at the start of
every new container:

```bash
west zephyr-export   # registers Zephyr in the CMake package registry
```

`west init -l config` only needs to run once ever — it persists into
`.west/` on the mounted repo. A later run reports "already initialized";
that's expected, skip straight to `west update`.

`build.sh` itself just runs [`scripts/build_from_matrix.py`](scripts/build_from_matrix.py)
inside the container, which parses `build.yaml` (supporting both the
top-level `board`/`shield` list form and the `include` form — see the
comments at the top of `build.yaml`) and runs one `west build` per
combination, equivalent to:

```bash
west build -s zmk/app -d build/left -b nice_nano//zmk -p -- \
  -DSHIELD="lily58_left nice_view_adapter nice_view" -DZMK_CONFIG=/workspace/config
```

- `-s zmk/app` points West at ZMK's application source (the same flag CI
  uses); without it, West doesn't know where the buildable app lives.
- `-b nice_nano//zmk` matches `config/west.yml`, which is pinned to a commit
  on ZMK's `main` branch. On the older `v0.3` tag, the board is instead
  named `nice_nano_v2` — `main` merged `nice_nano_v1`/`nice_nano_v2` into a
  single `nice_nano` board (revision `2.0.0` by default, exposed via the
  `zmk` variant), so `nice_nano_v2` no longer resolves there.
