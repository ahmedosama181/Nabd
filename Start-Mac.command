#!/bin/bash
# Nabd - double-click to start on macOS (also works on Linux from a terminal).
# Uses an installed Python 3.8+ if there is one; otherwise downloads a private, portable Python into ./runtime
# (no admin password, nothing installed system-wide).
cd "$(dirname "$0")" || exit 1

PBS_TAG="20260929"          # python-build-standalone release (github.com/astral-sh/python-build-standalone)
PBS_VER="3.12.14"
RUNTIME="runtime/python-mac"

usable() { "$1" -c 'import sys, ssl; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; }

find_python() {
  if [ -x "$RUNTIME/python/bin/python3" ] && usable "$RUNTIME/python/bin/python3"; then
    echo "$RUNTIME/python/bin/python3"; return 0
  fi
  for c in python3.13 python3.12 python3.11 python3.10 python3.9 python3; do
    p="$(command -v "$c" 2>/dev/null)" || continue
    # Apple's /usr/bin/python3 is only a placeholder until the developer tools are installed:
    # running it would pop up an install dialog, so skip it in that case.
    if [ "$p" = "/usr/bin/python3" ] && [ "$(uname)" = "Darwin" ] && ! xcode-select -p >/dev/null 2>&1; then continue; fi
    if usable "$p"; then echo "$p"; return 0; fi
  done
  return 1
}

install_python() {
  case "$(uname -s)-$(uname -m)" in
    Darwin-arm64)  triple="aarch64-apple-darwin" ;;
    Darwin-x86_64) triple="x86_64-apple-darwin" ;;
    *) echo "Automatic setup only covers macOS. Please install Python 3.8+ and try again."; return 1 ;;
  esac
  file="cpython-${PBS_VER}+${PBS_TAG}-${triple}-install_only.tar.gz"
  base="https://github.com/astral-sh/python-build-standalone/releases/download/${PBS_TAG}"
  tmp="$(mktemp -d)" || return 1
  echo "Python was not found. Setting up a private copy for Nabd - this happens only once (about 20 MB)..."
  curl -fsSL --retry 3 -o "$tmp/py.tar.gz" "$base/${file//+/%2B}" || { echo "Download failed."; rm -rf "$tmp"; return 1; }
  curl -fsSL --retry 3 -o "$tmp/SHA256SUMS" "$base/SHA256SUMS" || { echo "Could not download the checksum list."; rm -rf "$tmp"; return 1; }
  expected="$(grep -F "$file" "$tmp/SHA256SUMS" | grep -oE '[0-9a-f]{64}' | head -1)"
  actual="$(shasum -a 256 "$tmp/py.tar.gz" | awk '{print $1}')"
  if [ -z "$expected" ] || [ "$expected" != "$actual" ]; then
    echo "Checksum check failed - nothing was installed."; rm -rf "$tmp"; return 1
  fi
  rm -rf "$RUNTIME" && mkdir -p "$RUNTIME" && tar -xzf "$tmp/py.tar.gz" -C "$RUNTIME" || { rm -rf "$tmp"; return 1; }
  rm -rf "$tmp"
  echo "Python is ready."
}

PY="$(find_python)" || { install_python && PY="$(find_python)"; }
if [ -z "$PY" ]; then
  echo
  echo "Could not set up Python automatically. Check your internet connection and run this again,"
  echo "or install Python from https://www.python.org/downloads/ and run this again."
  read -r -p "Press Enter to close..." _
  exit 1
fi
"$PY" app.py
read -r -p "Stopped. Press Enter to close..." _
