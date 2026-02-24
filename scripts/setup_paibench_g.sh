#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_REPO="${REPO_ROOT}/external/physical-ai-bench"
GEN_DIR="${TARGET_REPO}/generation"

if ! command -v uv >/dev/null 2>&1; then
  echo "[ERROR] uv is not installed. Please install uv first: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

mkdir -p "${REPO_ROOT}/external"

if [ ! -d "${TARGET_REPO}/.git" ]; then
  echo "[INFO] Cloning physical-ai-bench into ${TARGET_REPO} ..."
  git clone https://github.com/SHI-Labs/physical-ai-bench.git "${TARGET_REPO}"
else
  echo "[INFO] Existing repo found at ${TARGET_REPO}, skipping clone."
fi

if [ ! -d "${GEN_DIR}" ]; then
  echo "[ERROR] generation directory not found: ${GEN_DIR}"
  exit 1
fi

pushd "${GEN_DIR}" >/dev/null

echo "[INFO] Installing generation dependencies with uv sync ..."
uv sync

echo "[INFO] Installing detectron2 ..."
uv pip install --no-build-isolation "git+https://github.com/facebookresearch/detectron2.git"

popd >/dev/null

echo "[OK] PAI-Bench-G environment setup complete."
