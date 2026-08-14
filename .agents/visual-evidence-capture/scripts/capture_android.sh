#!/usr/bin/env bash
# Capture a screenshot from a connected Android device or emulator.
#
# Usage:
#   bash capture_android.sh OUT.png [DEVICE_SERIAL]
#
# Works for Expo Go, a dev build, or a release APK — anything currently on screen.
# Use --list to see attached devices when more than one is connected.
set -euo pipefail

if [[ "${1:-}" == "--list" ]]; then
  adb devices -l
  exit 0
fi

OUT="${1:?Usage: capture_android.sh OUT.png [DEVICE_SERIAL]}"
SERIAL="${2:-}"
ADB=(adb)
[[ -n "$SERIAL" ]] && ADB=(adb -s "$SERIAL")

if ! command -v adb >/dev/null 2>&1; then
  echo "adb not found. Install Android platform-tools and ensure adb is on PATH." >&2
  exit 1
fi

COUNT=$("${ADB[@]}" devices | grep -c "device$" || true)
if [[ "$COUNT" -eq 0 ]]; then
  echo "No device detected. Start an emulator or connect a device with USB debugging enabled." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
"${ADB[@]}" exec-out screencap -p > "$OUT"

# Record the device context alongside the capture — screenshots are much less useful
# when the density and resolution they were taken at are unknown.
{
  echo "device: $("${ADB[@]}" shell getprop ro.product.model | tr -d '\r')"
  echo "android: $("${ADB[@]}" shell getprop ro.build.version.release | tr -d '\r')"
  echo "size: $("${ADB[@]}" shell wm size | tr -d '\r')"
  echo "density: $("${ADB[@]}" shell wm density | tr -d '\r')"
} > "${OUT%.png}.context.txt"

echo "Captured $OUT"
cat "${OUT%.png}.context.txt"
