#!/usr/bin/env python3
"""Build every board/shield combination listed in build.yaml.

Runs inside the zmk-build-arm container (invoked by build.sh). Mirrors how
ZMK's own build-user-config.yml GitHub Actions workflow reads build.yaml, so
build.sh and CI build the exact same set of targets from one source of
truth.
"""

import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_YAML = REPO_ROOT / "build.yaml"
ZMK_CONFIG = "/workspace/config"


def load_combinations():
    data = yaml.safe_load(BUILD_YAML.read_text()) or {}

    boards = data.get("board", [])
    shields = data.get("shield", [])
    if isinstance(boards, str):
        boards = [boards]
    if isinstance(shields, str):
        shields = [shields]

    combos = []
    for board in boards:
        if shields:
            for shield in shields:
                combos.append({"board": board, "shield": shield})
        else:
            combos.append({"board": board})

    for entry in data.get("include", []):
        combos.append(entry)

    return combos


def artifact_name(combo):
    if "artifact-name" in combo:
        return combo["artifact-name"]
    if "shield" in combo:
        return combo["shield"].split()[0]
    return combo["board"]


def build_one(combo):
    name = artifact_name(combo)
    build_dir = f"build/{name}"

    cmd = [
        "west",
        "build",
        "-s",
        "zmk/app",
        "-d",
        build_dir,
        "-b",
        combo["board"],
        "-p",
    ]

    if snippet := combo.get("snippet"):
        cmd += ["-S", snippet]

    cmd += ["--", f"-DZMK_CONFIG={ZMK_CONFIG}"]

    if shield := combo.get("shield"):
        cmd.append(f"-DSHIELD={shield}")

    if extra_args := combo.get("cmake-args"):
        cmd += extra_args.split()

    print(
        f"==> Building {name} (board={combo['board']}, shield={combo.get('shield', '-')})"
    )
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)

    uf2 = REPO_ROOT / build_dir / "zephyr" / "zmk.uf2"
    if not uf2.exists():
        print(f"Warning: expected {uf2} but it was not produced", file=sys.stderr)
        return None

    export_dir = REPO_ROOT / "export"
    export_dir.mkdir(exist_ok=True)
    dest = export_dir / f"{name}.uf2"
    dest.write_bytes(uf2.read_bytes())
    return dest


def main():
    combos = load_combinations()
    if not combos:
        print("No board/shield combinations found in build.yaml", file=sys.stderr)
        sys.exit(1)

    outputs = [build_one(combo) for combo in combos]

    print("\n==> Firmware built:")
    for path in outputs:
        if path:
            print(f"  {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
