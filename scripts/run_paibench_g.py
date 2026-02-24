#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
from pathlib import Path

VIDEO_NAME_PATTERN = re.compile(r"^.+__.+\.mp4$")

DIMENSIONS = [
    "aesthetic_quality",
    "background_consistency",
    "imaging_quality",
    "motion_smoothness",
    "overall_consistency",
    "subject_consistency",
    "i2v_background",
    "i2v_subject",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PAI-Bench-G evaluation on custom videos.")
    parser.add_argument("--run", action="store_true", help="Actually execute evaluation commands.")
    parser.add_argument("--check-only", action="store_true", help="Validate inputs and print commands only.")
    parser.add_argument("--only", choices=["quality", "vlm", "all"], default="all", help="Which stage to run.")
    parser.add_argument("--nproc-per-node", type=int, default=8, help="Number of processes for distributed quality eval.")
    parser.add_argument("--videos-dir", default="data/paibench_g/videos", help="Directory containing generated videos.")
    parser.add_argument("--dataset-dir", default="data/paibench_g/hf_dataset", help="HF dataset local directory.")
    parser.add_argument("--output-dir", default="data/paibench_g/results", help="Evaluation output directory.")
    parser.add_argument("--repo-dir", default="external/physical-ai-bench", help="physical-ai-bench repository path.")
    return parser.parse_args()


def validate_inputs(videos_dir: Path, dataset_dir: Path, repo_dir: Path) -> list[str]:
    errors: list[str] = []

    if not repo_dir.exists():
        errors.append(f"Repository not found: {repo_dir}")
    elif not (repo_dir / "generation" / "evaluate.py").exists():
        errors.append(f"Missing evaluate.py under: {repo_dir / 'generation'}")

    prompt_file = dataset_dir / "cosmos_predict2_bench_full_info.json"
    condition_image = dataset_dir / "condition_image"
    vqa_dir = dataset_dir / "vqa"

    if not prompt_file.exists():
        errors.append(f"Missing prompt file: {prompt_file}")
    if not condition_image.is_dir():
        errors.append(f"Missing condition image directory: {condition_image}")
    if not vqa_dir.is_dir():
        errors.append(f"Missing VQA directory: {vqa_dir}")

    if not videos_dir.is_dir():
        errors.append(f"Videos directory not found: {videos_dir}")
    else:
        video_files = sorted(videos_dir.glob("*.mp4"))
        if not video_files:
            errors.append(f"No .mp4 files found in: {videos_dir}")
        invalid = [f.name for f in video_files if not VIDEO_NAME_PATTERN.match(f.name)]
        if invalid:
            errors.append(
                "Invalid video filename(s), expected {video_id}__{seed}.mp4: "
                + ", ".join(invalid[:10])
                + (" ..." if len(invalid) > 10 else "")
            )

    return errors


def run_command(cmd: list[str], cwd: Path) -> None:
    printable = " ".join(shlex.quote(x) for x in cmd)
    print(f"[CMD] (cd {cwd} && {printable})")
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    args = parse_args()

    if args.run and args.check_only:
        raise SystemExit("Use either --run or --check-only, not both.")

    run_mode = args.run
    if not args.run and not args.check_only:
        print("[INFO] Neither --run nor --check-only provided; defaulting to check-only mode.")

    videos_dir = Path(args.videos_dir).resolve()
    dataset_dir = Path(args.dataset_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    repo_dir = Path(args.repo_dir).resolve()
    generation_dir = repo_dir / "generation"

    errors = validate_inputs(videos_dir=videos_dir, dataset_dir=dataset_dir, repo_dir=repo_dir)
    if errors:
        print("[ERROR] Input validation failed:")
        for item in errors:
            print(f"  - {item}")
        raise SystemExit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    quality_cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "torch.distributed.run",
        "--standalone",
        "--nproc_per_node",
        str(args.nproc_per_node),
        "evaluate.py",
        "--mode",
        "custom_input",
        "--prompt_file",
        str(dataset_dir / "cosmos_predict2_bench_full_info.json"),
        "--custom_image_folder",
        str(dataset_dir / "condition_image"),
        "--dimension",
        *DIMENSIONS,
        "--videos_path",
        str(videos_dir),
        "--output_path",
        str(output_dir),
    ]

    vlm_cmd = [
        "uv",
        "run",
        "python",
        "evaluate_vqa.py",
        "--prompt_file",
        str(dataset_dir / "cosmos_predict2_bench_full_info.json"),
        "--vqa_questions_dir",
        str(dataset_dir / "vqa"),
        "--video_dir",
        str(videos_dir),
        "--output_dir",
        str(output_dir),
    ]

    stages = ["quality", "vlm"] if args.only == "all" else [args.only]

    print("[INFO] Input validation passed.")
    print(f"[INFO] Videos: {videos_dir}")
    print(f"[INFO] Dataset: {dataset_dir}")
    print(f"[INFO] Output: {output_dir}")
    print(f"[INFO] Mode: {'run' if run_mode else 'check-only'}")

    if "quality" in stages:
        if run_mode:
            run_command(quality_cmd, cwd=generation_dir)
        else:
            print("[PLAN] Quality evaluation command:")
            print("       " + " ".join(shlex.quote(x) for x in quality_cmd))

    if "vlm" in stages:
        if run_mode:
            run_command(vlm_cmd, cwd=generation_dir)
        else:
            print("[PLAN] VLM judge command:")
            print("       " + " ".join(shlex.quote(x) for x in vlm_cmd))


if __name__ == "__main__":
    main()
