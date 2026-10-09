"""Create a model-neutral, reviewable prompt manifest for one scene."""
from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "1.0"
SPACE_EN = {
    "한옥 마루": "the warm wooden floor of a traditional Korean hanok",
    "한옥 창호": "a traditional Korean hanok window with wooden lattice doors",
    "비 오는 창가": "a quiet window beside gentle rain",
    "해변 노을": "a peaceful beach at sunset",
}
PRESETS = {
    "local_preview": {"width_landscape": 854, "height_landscape": 480, "width_portrait": 480, "height_portrait": 854},
    "standard_scene": {"width_landscape": 1280, "height_landscape": 720, "width_portrait": 720, "height_portrait": 1280},
    "premium_scene": {"width_landscape": 1920, "height_landscape": 1080, "width_portrait": 1080, "height_portrait": 1920},
}


def build_manifest(job_id: str, payload: dict[str, Any], created_at: str) -> dict[str, Any]:
    kind = payload.get("kind", "long")
    portrait = kind == "shorts"
    profile = PRESETS[payload["preset"]]
    width = profile["width_portrait" if portrait else "width_landscape"]
    height = profile["height_portrait" if portrait else "height_landscape"]
    place = SPACE_EN.get(payload["space"], payload["space"])
    framing = (
        "Vertical 9:16 composition, subject centered within the safe area."
        if portrait else "Horizontal 16:9 composition with generous negative space."
    )
    prompt = (
        f"A quiet, soothing meditation scene in {place}. {framing} "
        "A peaceful domestic cat rests naturally in the scene, with a consistent coat, "
        "face, paws, and proportions. Locked-off camera, only barely perceptible natural "
        "movement, soft diffused light, muted warm colors, low visual contrast, "
        "unhurried and restful atmosphere, loop-friendly ending. No cuts."
    )
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
        "scene": {
            "sceneId": "scene-001",
            "durationSecondsTarget": 6 if portrait else 8,
            "frameRateTarget": 16,
            "widthTarget": width,
            "heightTarget": height,
            "resolutionIsTargetOnly": True,
            "positivePromptDraft": prompt,
            "negativePromptDraft": negative_prompt,
            "promptRequiresHumanReview": True,
        },
        "execution": {
            "profile": payload["preset"],
            "modelId": None,
            "worker": None,
            "seed": None,
            "status": "draft_only",
            "inferenceStarted": False,
            "note": "This is a reviewed prompt/settings draft, not a generated video. No model is configured yet.",
        },
        "audio": {
            "mixDirection": payload["bed"],
            "audioFile": None,
            "licenseVerified": False,
            "note": "No audio is attached. Add only an independently rights-verified track during the later assembly stage.",
        },
    }
