"""Reviewed initial Wan model mapping and conservative GPU requirements."""
from __future__ import annotations

from typing import Any

MODEL_BY_PRESET: dict[str, dict[str, Any]] = {
    "local_preview": {
        "modelId": "Wan-AI/Wan2.1-T2V-1.3B",
        "name": "Wan2.1 T2V 1.3B",
        "task": "text-to-video",
        "repository": "https://github.com/Wan-Video/Wan2.1",
        "modelCard": "https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B",
        "resolution": "832*480",
        "frameRate": 16,
        "minVramGb": 8.19,
        "targetGpu": "RTX 3070 8GB",
        "license": "Apache-2.0 (verify the exact checkpoint and dependencies before commercial use)",
        "checkpointDir": "models/Wan2.1-T2V-1.3B",
        "taskArg": "t2v-1.3B",
        "referenceImageRequired": False,
        "risk": "RTX 3070 8GB is borderline against the model card's 8.19 GB figure; use CPU offload and T5 on CPU. OOM is possible and free VRAM must be measured.",
    },
    "standard_scene": {
        "modelId": "Wan-AI/Wan2.2-TI2V-5B",
        "name": "Wan2.2 TI2V 5B",
        "task": "text-image-to-video",
        "repository": "https://github.com/Wan-Video/Wan2.2",
        "modelCard": "https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B",
        "resolution": "1280*704",
        "frameRate": 24,
        "minVramGb": 24,
        "targetGpu": "A100 MIG 40GB",
        "license": "Apache-2.0 (verify the exact checkpoint and dependencies before commercial use)",
        "checkpointDir": "models/Wan2.2-TI2V-5B",
        "taskArg": "ti2v-5B",
        "referenceImageRequired": False,
        "risk": "Official single-GPU instructions specify at least 24 GB VRAM; confirm the MIG slice exposes sufficient usable memory.",
    },
    "premium_scene": {
        "modelId": "Wan-AI/Wan2.2-I2V-A14B",
        "name": "Wan2.2 I2V A14B",
        "task": "image-to-video",
        "repository": "https://github.com/Wan-Video/Wan2.2",
        "modelCard": "https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B",
        "resolution": "1280*720",
        "frameRate": 24,
        "minVramGb": 80,
        "targetGpu": "H100 SXM 80GB",
        "license": "Apache-2.0 (verify the exact checkpoint and dependencies before commercial use)",
        "checkpointDir": "models/Wan2.2-I2V-A14B",
        "taskArg": "i2v-A14B",
        "referenceImageRequired": True,
        "risk": "Official single-GPU instructions specify at least 80 GB VRAM; leave headroom and use the official offload/dtype-conversion flags.",
    },
}


# nvidia-smi reports MiB while vendor/model cards round VRAM to GB; allow 1% unit/rounding tolerance.
VRAM_REFERENCE_TOLERANCE = 0.99


def model_for_preset(preset: str) -> dict[str, Any]:
    """Return a defensive copy of the reviewed model mapping."""
    if preset not in MODEL_BY_PRESET:
        raise ValueError("지원하지 않는 GPU 프리셋입니다.")
    return dict(MODEL_BY_PRESET[preset])


def describe_compatibility(preset: str, gpu_memory_gb: float | None) -> dict[str, Any]:
    model = model_for_preset(preset)
    if gpu_memory_gb is None:
        status = "unknown"
    elif gpu_memory_gb < model["minVramGb"] * VRAM_REFERENCE_TOLERANCE:
        status = "below_reference"
    else:
        status = "meets_reference"
    return {
        **model,
        "detectedVramGb": gpu_memory_gb,
        "compatibility": status,
    }
