"""Create a model-neutral, reviewable storyboard prompt manifest."""
from __future__ import annotations

from typing import Any

try:
    from .models import model_for_preset
except ImportError:  # Support direct execution from server.py.
    from models import model_for_preset

SCHEMA_VERSION = "1.2"
SPACE_EN = {
    "한옥 마루": "the warm wooden floor of a traditional Korean hanok",
    "한옥 창호": "a traditional Korean hanok window with wooden lattice doors",
    "비 오는 창가": "a quiet window beside gentle rain",
    "해변 노을": "a peaceful beach at sunset",
}
PRESETS = {
    "local_preview": {"width_landscape": 832, "height_landscape": 480, "width_portrait": 480, "height_portrait": 832},
    "standard_scene": {"width_landscape": 1280, "height_landscape": 704, "width_portrait": 704, "height_portrait": 1280},
    "premium_scene": {"width_landscape": 1280, "height_landscape": 720, "width_portrait": 720, "height_portrait": 1280},
}


def build_manifest(job_id: str, payload: dict[str, Any], created_at: str) -> dict[str, Any]:
    kind = payload.get("kind", "long")
    portrait = kind == "shorts"
    profile = PRESETS[payload["preset"]]
    width = profile["width_portrait" if portrait else "width_landscape"]
    height = profile["height_portrait" if portrait else "height_landscape"]
    place = SPACE_EN.get(payload["space"], payload["space"])
    selected_model = model_for_preset(payload["preset"])
    framing = (
        "Vertical 9:16 composition, subject centered within the safe area."
        if portrait else "Horizontal 16:9 composition with generous negative space."
    )
    cat_identity = (
        "The same peaceful domestic cat throughout: consistent coat pattern, face, "
        "paws, and proportions."
    )
    scene_specs = [
        ("wide-establishing", "The cat rests curled near the window; establish the room."),
        ("gentle-detail", "A calm closer view as the cat slowly blinks once."),
        ("quiet-return", "Return to the resting composition; only a subtle tail movement."),
    ]
    negative_prompt = (
        "text, captions, logo, watermark, people, extra animals, deformed cat, "
        "changing fur pattern, malformed paws, extra limbs, distorted architecture, "
        "camera shake, fast motion, sudden zoom, rapid cuts, flicker, flashing lights, "
        "high contrast, oversaturated colors, horror, dramatic action"
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "jobId": job_id,
        "createdAt": created_at,
        "item": {
            "itemId": payload["itemId"],
            "title": payload["title"],
            "pillar": payload["pillar"],
            "kind": kind,
            "plannedFinalVideoMinutes": payload["minutes"],
        },
        "creativeBrief": {
            "spaceKo": payload["space"],
            "visualSettingDraftEn": place,
            "musicDirection": payload["bed"],
            "brandRules": [
                "Calm, slow, and visually restrained.",
                "Keep the cat and environment visually consistent.",
                "Do not generate text or logos in the image model.",
                "Human review is required before a clip is approved."
            ],
        },
        "storyboard": {
            "scope": "three short scene previews only; this does not generate the planned final video duration",
            "scenes": [
                {
                    "sceneId": f"scene-{index:03d}",
                    "shot": shot,
                    "durationSecondsTarget": 6 if portrait else 8,
                    "frameRateTarget": selected_model["frameRate"],
                    "widthTarget": width,
                    "heightTarget": height,
                    "resolutionIsTargetOnly": True,
                    "positivePromptDraft": (
                        f"A quiet, soothing meditation scene in {place}. {framing} "
                        f"{action} {cat_identity} Locked-off camera, barely perceptible "
                        "natural movement, soft diffused light, muted warm colors, low "
                        "visual contrast, unhurried atmosphere. No cuts."
                    ),
                    "negativePromptDraft": negative_prompt,
                    "promptRequiresHumanReview": True,
                }
                for index, (shot, action) in enumerate(scene_specs, start=1)
            ],
        },
        "modelSelection": {
            "modelId": selected_model["modelId"],
            "name": selected_model["name"],
            "modelCard": selected_model["modelCard"],
            "repository": selected_model["repository"],
            "targetGpu": selected_model["targetGpu"],
            "referenceMinimumVramGb": selected_model["minVramGb"],
            "license": selected_model["license"],
            "validationStatus": "not_run",
            "risk": selected_model["risk"],
        },
        "execution": {
            "profile": payload["preset"],
            "modelId": selected_model["modelId"],
            "worker": None,
            "seed": None,
            "status": "draft_only",
            "inferenceStarted": False,
            "note": "Model mapped for validation only. This is not a generated video; run the local smoke-test tool to validate inference.",
        },
        "audio": {
            "mixDirection": payload["bed"],
            "audioFile": None,
            "licenseVerified": False,
            "note": "No audio is attached. Add only an independently rights-verified track during the later assembly stage.",
        },
    }
