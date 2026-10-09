"""Preflight or run one conservative, short official Wan inference test."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from .models import MODEL_BY_PRESET, VRAM_REFERENCE_TOLERANCE, model_for_preset
except ImportError:  # Support direct execution from the project root.
    from models import MODEL_BY_PRESET, VRAM_REFERENCE_TOLERANCE, model_for_preset

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROMPT = (
    "A calm domestic cat resting on a warm wooden hanok floor beside a window, "
    "soft diffused morning light, locked camera, subtle natural movement, "
    "muted warm colors, no text, no logo."
)


def read_gpu() -> dict[str, str] | None:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    name, total, free = result.stdout.strip().splitlines()[0].split(",", maxsplit=2)
    return {"name": name.strip(), "totalMiB": total.strip(), "freeMiB": free.strip()}


def build_command(
    preset: str,
    repo_dir: Path,
    checkpoint_dir: Path,
    output_path: Path,
    prompt: str,
    image_path: Path | None = None,
) -> list[str]:
    model = model_for_preset(preset)
    command = [
        sys.executable, "generate.py",
        "--task", model["taskArg"],
        "--size", model["resolution"],
        "--frame_num", "17",
        "--ckpt_dir", str(checkpoint_dir.resolve()),
        "--save_file", str(output_path.resolve()),
        "--offload_model", "True",
        "--t5_cpu",
        "--prompt", prompt,
    ]
    if preset != "local_preview":
        command.append("--convert_model_dtype")
    if preset == "local_preview":
        command.extend(["--sample_shift", "8", "--sample_guide_scale", "6"])
    if model["referenceImageRequired"]:
        if image_path is None:
            raise ValueError("Wan2.2 I2V 테스트에는 시작 이미지가 필요합니다. --image를 지정하세요.")
        command.extend(["--image", str(image_path.resolve())])
    return command


def check_torch_cuda() -> tuple[bool, str]:
    probe = subprocess.run(
        [sys.executable, "-c", "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no CUDA device')"],
        capture_output=True, text=True, timeout=20, check=False,
    )
    if probe.returncode != 0:
        return False, (probe.stderr.strip() or "PyTorch 확인 실패")
    return "True" in probe.stdout.splitlines()[1:2], probe.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=sorted(MODEL_BY_PRESET), required=True)
    parser.add_argument("--repo-dir", type=Path, required=True, help="공식 Wan2.1 또는 Wan2.2 저장소 경로")
    parser.add_argument("--checkpoint-dir", type=Path, required=True, help="모델 가중치 디렉터리")
    parser.add_argument("--image", type=Path, help="I2V 모델에 사용할 검토된 시작 이미지")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--run", action="store_true", help="사전 점검 후 실제 추론 실행; 기본값은 점검만")
    parser.add_argument("--allow-vram-risk", action="store_true", help="기준 VRAM 미달이어도 사용자가 위험을 인지하고 실행")
    args = parser.parse_args()

    model = model_for_preset(args.preset)
    repo_dir = args.repo_dir.resolve()
    checkpoint_dir = args.checkpoint_dir.resolve()
    image_path = args.image.resolve() if args.image else None
    report: dict[str, object] = {
        "modelId": model["modelId"],
        "modelCard": model["modelCard"],
        "targetGpu": model["targetGpu"],
        "referenceMinimumVramGb": model["minVramGb"],
        "risk": model["risk"],
    }
    gpu = read_gpu()
    report["gpu"] = gpu
    if gpu:
        free_gb = int(gpu["freeMiB"]) / 1024
        total_gb = int(gpu["totalMiB"]) / 1024
        report["totalVramGb"] = round(total_gb, 2)
        report["freeVramGb"] = round(free_gb, 2)
    cuda_ok, torch_info = check_torch_cuda()
    report["torchCuda"] = torch_info
    report["sourceRepo"] = str(repo_dir)
    report["checkpointDir"] = str(checkpoint_dir)
    report["sourceReady"] = (repo_dir / "generate.py").is_file()
    report["checkpointReady"] = checkpoint_dir.is_dir() and any(checkpoint_dir.iterdir())
    if model["referenceImageRequired"]:
        if image_path is None and (repo_dir / "examples" / "i2v_input.JPG").is_file():
            image_path = repo_dir / "examples" / "i2v_input.JPG"
        report["image"] = str(image_path) if image_path else None
        report["imageReady"] = bool(image_path and image_path.is_file())
    else:
        report["imageReady"] = True

    errors = []
    if not gpu:
        errors.append("nvidia-smi에서 NVIDIA GPU를 확인할 수 없습니다.")
    if not cuda_ok:
        errors.append("현재 Python 환경에서 CUDA PyTorch를 사용할 수 없습니다.")
    if not report["sourceReady"]:
        errors.append("repo-dir에 공식 저장소의 generate.py가 없습니다.")
    if not report["checkpointReady"]:
        errors.append("checkpoint-dir가 없거나 비어 있습니다.")
    if not report["imageReady"]:
        errors.append("I2V 입력 이미지가 없습니다.")
    if gpu and total_gb < model["minVramGb"] * VRAM_REFERENCE_TOLERANCE:
        report["compatibility"] = "below_reference"
        if not args.allow_vram_risk:
            errors.append("GPU VRAM이 모델 카드 기준보다 작습니다. --allow-vram-risk 없이는 추론을 차단합니다.")
    else:
        report["compatibility"] = "meets_reference" if gpu else "unknown"

    output_dir = ROOT / "runtime" / "model-tests"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"{args.preset}-{stamp}.mp4"
    log_path = output_dir / f"{args.preset}-{stamp}.log"
    report["outputPath"] = str(output_path)
    report["logPath"] = str(log_path)
    if not errors:
        try:
            command = build_command(args.preset, repo_dir, checkpoint_dir, output_path, args.prompt, image_path)
            report["command"] = command
        except ValueError as exc:
            errors.append(str(exc))

    report["errors"] = errors
    if errors:
        report["result"] = "blocked"
    elif not args.run:
        report["result"] = "preflight_passed_not_generated"
    else:
        env = os.environ.copy()
        env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        report["result"] = "running"
        with log_path.open("w", encoding="utf-8") as log:
            completed = subprocess.run(
                report["command"], cwd=repo_dir, env=env,
                stdout=log, stderr=subprocess.STDOUT, check=False,
            )
        report["exitCode"] = completed.returncode
        report["result"] = "generated" if completed.returncode == 0 and output_path.is_file() and output_path.stat().st_size else "failed"
        if report["result"] == "failed":
            report["errors"] = ["추론이 실패했거나 비어 있는 결과 파일입니다. 작업 로그를 확인하세요."]

    report_path = output_dir / f"{args.preset}-{stamp}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["result"] in {"preflight_passed_not_generated", "generated"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
