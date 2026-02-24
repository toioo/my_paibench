# PAI-Bench 复现（先实现 G: Video Generation）

这个仓库当前先实现 **PAI-Bench-G** 的本地可复现评测流程，目标是：
- 你把自己的生成视频放到指定目录；
- 运行一条命令完成质量评测和 VLM Judge 评测；
- 结果输出到固定目录，便于后续汇总。

> 你在服务器上使用时，会在 `/DATA/wangyuanfei/jf/paibench` 下 `git clone` 本仓库。本文所有路径都以仓库根目录（`paibench`）为基准，确保和其他任务文件夹隔离。

## 目录约定（你只需要往这里放数据）

请把数据放在以下位置：

```text
paibench/
├── data/paibench_g/
│   ├── hf_dataset/
│   │   ├── cosmos_predict2_bench_full_info.json
│   │   ├── condition_image/
│   │   └── vqa/
│   ├── videos/
│   │   ├── {video_id}__{seed}.mp4
│   │   └── ...
│   └── results/
├── external/
└── scripts/
```

其中：
- `data/paibench_g/hf_dataset/`：放从 Hugging Face `physical-ai-bench-generation` 下载的数据。
- `data/paibench_g/videos/`：放你模型生成的视频，命名必须是 `{video_id}__{seed}.mp4`。
- `data/paibench_g/results/`：评测输出目录（可为空，脚本会自动创建）。

## 一次性环境准备（会创建独立 conda 环境）

```bash
bash scripts/setup_paibench_g.sh
```

该脚本会：
1. 将官方仓库克隆到 `external/physical-ai-bench`（若已存在则跳过克隆）；
2. 创建一个新的 conda 环境（默认名：`paibench-g`，可通过环境变量修改）；
3. 在该 conda 环境中安装 `uv`；
4. 在 `external/physical-ai-bench/generation` 下执行依赖安装：
   - `uv sync --active`
   - `uv pip install --python "$(which python)" --no-build-isolation "git+https://github.com/facebookresearch/detectron2.git"`

### 可选：自定义环境名和 Python 版本

```bash
PAIBENCH_CONDA_ENV=paibench-g-cu121 PAIBENCH_PYTHON_VERSION=3.10 bash scripts/setup_paibench_g.sh
```

## 运行评测（请在新 conda 环境中运行）

```bash
conda activate paibench-g
```

### 1) 先做本地检查（不执行评测）

```bash
python scripts/run_paibench_g.py --check-only
```

### 2) 执行完整评测（质量 + VLM Judge）

```bash
python scripts/run_paibench_g.py --run
```

### 3) 只跑质量评测

```bash
python scripts/run_paibench_g.py --run --only quality
```

### 4) 只跑 VLM Judge

```bash
python scripts/run_paibench_g.py --run --only vlm
```

## 可选参数

- `--nproc-per-node`：质量评测使用的进程数（默认 `8`）
- `--videos-dir`：自定义视频目录（默认 `data/paibench_g/videos`）
- `--dataset-dir`：自定义数据集目录（默认 `data/paibench_g/hf_dataset`）
- `--output-dir`：自定义结果目录（默认 `data/paibench_g/results`）
- `--repo-dir`：官方仓库路径（默认 `external/physical-ai-bench`）

示例：

```bash
python scripts/run_paibench_g.py --run --nproc-per-node 4
```

## 常见问题

1. **视频命名不符合规范**
   - 必须是 `{video_id}__{seed}.mp4`，例如 `12345__0.mp4`。

2. **缺少数据文件**
   - 确认 `data/paibench_g/hf_dataset` 下有：
     - `cosmos_predict2_bench_full_info.json`
     - `condition_image/`
     - `vqa/`

3. **显卡资源不足**
   - 降低 `--nproc-per-node`，如 `1` 或 `2`。
