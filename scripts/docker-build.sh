#!/usr/bin/env bash
# ZMK firmware Docker build script
# Usage:
#   ./scripts/docker-build.sh init                  - Initialize west workspace (run once)
#   ./scripts/docker-build.sh build all             - Build all targets
#   ./scripts/docker-build.sh build cornix_left     - Build specific target by artifact name
#   ./scripts/docker-build.sh clean                 - Remove build cache and firmware output
#
# Requirements: docker (no nix, just, or yq needed)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_WS="$REPO_ROOT/.docker-workspace"
BUILD_DIR="$REPO_ROOT/.build"
FIRMWARE_DIR="$REPO_ROOT/output"
ZMK_IMAGE="zmkfirmware/zmk-build-arm:stable"
ZMK_CONFIG="/zmk-config/config2"

# Build target definitions from build.yaml
# Format: "artifact_name|board|shield|snippet"
TARGETS=(
    "cornix_left_default_nosd|cornix_left||"
    "cornix_left_for_dongle_nosd|cornix_ph_left||"
    "cornix_right_nosd|cornix_right||"
    "cornix_reset|cornix_right|settings_reset|studio-rpc-usb-uart nrf52840-nosd"
    "reset_nicenano_nosd|nice_nano//zmk|settings_reset|studio-rpc-usb-uart nrf52840-nosd"
)

usage() {
    grep '^# ' "$0" | sed 's/^# //' | head -10
    exit 1
}

cmd_init() {
    echo "==> Initializing Docker west workspace at $DOCKER_WS"
    mkdir -p "$DOCKER_WS"

    # Copy config/ into workspace so west can create .west/ there (not in repo)
    # config/west.yml defines the ZMK manifest
    docker run --rm \
        -v "$DOCKER_WS:/workspace" \
        -v "$REPO_ROOT/config:/repo-config:ro" \
        "$ZMK_IMAGE" \
        bash -c "
            set -e
            git config --global --add safe.directory '*'
            cd /workspace
            if [[ -d .west ]]; then
                echo 'Workspace already initialized, running west update...'
                west update --fetch-opt=--filter=blob:none
            else
                echo 'Copying manifest config...'
                cp -r /repo-config /workspace/config
                west init -l /workspace/config
                west update --fetch-opt=--filter=blob:none
            fi
            echo 'Done.'
        "

    echo "==> Docker workspace ready."
}

build_single() {
    local artifact="$1" board="$2" shield="$3" snippet="$4"
    local build_dir="$BUILD_DIR/$artifact"
    mkdir -p "$build_dir" "$FIRMWARE_DIR"

    # Match GitHub CI: ZMK_CONFIG=config/, ZMK_EXTRA_MODULES=repo root (for board_root via zephyr/module.yml)
    local cmake_args="-DZMK_CONFIG=/zmk-config/config -DZMK_EXTRA_MODULES=/zmk-config"

    local shield_arg=""
    [[ -n "$shield" ]] && shield_arg="-DSHIELD=\"$shield\""

    # Split space-separated snippets into multiple -S flags (e.g. "a b" -> "-S a -S b")
    local snippet_arg=""
    if [[ -n "$snippet" ]]; then
        for s in $snippet; do
            snippet_arg="$snippet_arg -S $s"
        done
    fi

    echo ""
    echo "==> Building: $artifact (board=$board, shield=${shield:-none}, snippet=${snippet:-none})"

    docker run --rm \
        -v "$DOCKER_WS:/workspace" \
        -v "$REPO_ROOT:/zmk-config:ro" \
        -v "$build_dir:/build" \
        -v "$FIRMWARE_DIR:/firmware" \
        "$ZMK_IMAGE" \
        bash -c "
            set -e
            git config --global --add safe.directory '*'
            export ZEPHYR_BASE=/workspace/zephyr
            export CMAKE_PREFIX_PATH=/workspace/zephyr/share/zephyr-package/cmake
            cd /workspace
            eval west build \\
                -s zmk/app \\
                -d /build \\
                -b '$board' \\
                $snippet_arg \\
                -- $cmake_args $shield_arg
            if [[ -f /build/zephyr/zmk.uf2 ]]; then
                cp /build/zephyr/zmk.uf2 /firmware/$artifact.uf2
                echo 'Saved /firmware/$artifact.uf2'
            else
                cp /build/zephyr/zmk.bin /firmware/$artifact.bin
                echo 'Saved /firmware/$artifact.bin'
            fi
        "
}

cmd_build() {
    local expr="${1:-all}"

    if [[ ! -d "$DOCKER_WS/.west" ]]; then
        echo "ERROR: Docker workspace not initialized. Run: $0 init" >&2
        exit 1
    fi

    local matched=0
    for target_def in "${TARGETS[@]}"; do
        IFS='|' read -r artifact board shield snippet <<< "$target_def"
        if [[ "$expr" == "all" ]] || [[ "$artifact" == *"$expr"* ]] || [[ "$board" == *"$expr"* ]]; then
            build_single "$artifact" "$board" "$shield" "$snippet"
            matched=$((matched + 1))
        fi
    done

    if [[ $matched -eq 0 ]]; then
        echo "ERROR: No matching targets for '$expr'. Available targets:" >&2
        for target_def in "${TARGETS[@]}"; do
            IFS='|' read -r artifact board _ _ <<< "$target_def"
            echo "  $artifact  (board: $board)" >&2
        done
        exit 1
    fi

    echo ""
    echo "==> Build complete. $matched target(s) built."
    ls -lh "$FIRMWARE_DIR"/*.uf2 "$FIRMWARE_DIR"/*.bin 2>/dev/null || true
}

cmd_clean() {
    echo "==> Cleaning $BUILD_DIR and $FIRMWARE_DIR"
    rm -rf "$BUILD_DIR" "$FIRMWARE_DIR"
    echo "Done."
}

cmd_list() {
    echo "Available build targets:"
    for target_def in "${TARGETS[@]}"; do
        IFS='|' read -r artifact board shield snippet <<< "$target_def"
        echo "  $artifact"
        echo "    board=${board}, shield=${shield:-none}, snippet=${snippet:-none}"
    done
}

case "${1:-}" in
    init)   cmd_init ;;
    build)  cmd_build "${2:-all}" ;;
    clean)  cmd_clean ;;
    list)   cmd_list ;;
    *)      usage ;;
esac
