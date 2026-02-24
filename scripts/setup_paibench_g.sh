#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_REPO="${REPO_ROOT}/external/physical-ai-bench"
GEN_DIR="${TARGET_REPO}/generation"
CONDA_ENV_NAME="${PAIBENCH_CONDA_ENV:-paibench-g}"
PYTHON_VERSION="${PAIBENCH_PYTHON_VERSION:-3.10}"

if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] conda command not found. Please install Miniconda/Anaconda first."
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

if conda env list | awk '{print $1}' | grep -Fxq "${CONDA_ENV_NAME}"; then
  echo "[INFO] Conda env '${CONDA_ENV_NAME}' already exists, skipping creation."
else
  echo "[INFO] Creating conda env '${CONDA_ENV_NAME}' (python=${PYTHON_VERSION}) ..."
  conda create -y -n "${CONDA_ENV_NAME}" "python=${PYTHON_VERSION}"
fi

echo "[INFO] Installing uv into conda env '${CONDA_ENV_NAME}' ..."
conda run -n "${CONDA_ENV_NAME}" python -m pip install --upgrade pip uv

echo "[INFO] Installing generation dependencies with uv sync --active ..."
conda run -n "${CONDA_ENV_NAME}" bash -lc "cd '${GEN_DIR}' && uv sync --active"

echo "[INFO] Installing detectron2 ..."
conda run -n "${CONDA_ENV_NAME}" bash -lc "cd '${GEN_DIR}' && uv pip install --python \"\$(which python)\" --no-build-isolation 'git+https://github.com/facebookresearch/detectron2.git'"

cat <<MSG
[OK] PAI-Bench-G environment setup complete.

请后续都在 conda 环境 '${CONDA_ENV_NAME}' 中运行，例如：
  conda activate ${CONDA_ENV_NAME}
  python scripts/run_paibench_g.py --check-only
  python scripts/run_paibench_g.py --run
MSG
