"""Regression tests for the model-neutral storyboard manifest."""
import unittest

from video_app.manifest import build_manifest
from video_app.models import describe_compatibility, model_for_preset


class BuildManifestTests(unittest.TestCase):
    def setUp(self):
        self.base_payload = {
            "itemId": "pilot-short",
            "title": "창틀 고양이",
            "pillar": "Sh",
            "space": "한옥 창호",
            "bed": "소프트 피아노",
            "minutes": 45,
            "preset": "local_preview",
        }

    def test_shorts_get_portrait_storyboard_and_no_inference_claim(self):
        manifest = build_manifest(
            "job-1", {**self.base_payload, "kind": "shorts", "minutes": 0.5}, "2026-09-13T00:00:00+00:00"
        )

        scenes = manifest["storyboard"]["scenes"]
        self.assertEqual(len(scenes), 3)
        self.assertEqual(scenes[0]["widthTarget"], 480)
        self.assertEqual(scenes[0]["heightTarget"], 832)
        self.assertEqual(scenes[0]["durationSecondsTarget"], 6)
        self.assertFalse(manifest["execution"]["inferenceStarted"])
        self.assertEqual(manifest["execution"]["modelId"], "Wan-AI/Wan2.1-T2V-1.3B")
        self.assertEqual(manifest["modelSelection"]["validationStatus"], "not_run")
        self.assertIsNone(manifest["audio"]["audioFile"])
        self.assertIn("does not generate", manifest["storyboard"]["scope"])

    def test_long_form_gets_landscape_scenes_and_consistent_guardrails(self):
        manifest = build_manifest(
            "job-2", self.base_payload, "2026-09-13T00:00:00+00:00"
        )

        scenes = manifest["storyboard"]["scenes"]
        self.assertEqual(scenes[0]["widthTarget"], 832)
        self.assertEqual(scenes[0]["heightTarget"], 480)
        self.assertEqual(scenes[0]["durationSecondsTarget"], 8)
        self.assertEqual(scenes[0]["frameRateTarget"], 16)
        self.assertEqual(len({scene["negativePromptDraft"] for scene in scenes}), 1)
        self.assertTrue(all(scene["promptRequiresHumanReview"] for scene in scenes))
        self.assertEqual(manifest["item"]["plannedFinalVideoMinutes"], 45)

    def test_unknown_space_is_preserved_as_draft_setting(self):
        payload = {**self.base_payload, "space": "사용자 지정 공간"}
        manifest = build_manifest("job-3", payload, "now")
        self.assertEqual(manifest["creativeBrief"]["visualSettingDraftEn"], "사용자 지정 공간")
        self.assertIn("사용자 지정 공간", manifest["storyboard"]["scenes"][0]["positivePromptDraft"])


class ModelMappingTests(unittest.TestCase):
    def test_requested_model_mapping(self):
        self.assertEqual(model_for_preset("local_preview")["modelId"], "Wan-AI/Wan2.1-T2V-1.3B")
        self.assertEqual(model_for_preset("standard_scene")["modelId"], "Wan-AI/Wan2.2-TI2V-5B")
        self.assertEqual(model_for_preset("premium_scene")["modelId"], "Wan-AI/Wan2.2-I2V-A14B")

    def test_vram_risk_is_not_silently_approved(self):
        self.assertEqual(describe_compatibility("local_preview", 8)["compatibility"], "below_reference")
        self.assertEqual(describe_compatibility("standard_scene", 40)["compatibility"], "meets_reference")
        self.assertEqual(describe_compatibility("premium_scene", 80)["compatibility"], "meets_reference")
        self.assertEqual(describe_compatibility("premium_scene", None)["compatibility"], "unknown")

    def test_manifest_uses_supported_model_sizes_and_frame_rates(self):
        cases = (
            ("local_preview", "long", 832, 480, 16),
            ("standard_scene", "long", 1280, 704, 24),
            ("premium_scene", "long", 1280, 720, 24),
        )
        for preset, kind, width, height, fps in cases:
            with self.subTest(preset=preset):
                payload = {
                    "itemId": "item", "title": "title", "pillar": "M",
                    "space": "한옥 마루", "bed": "피아노", "minutes": 10,
                    "preset": preset, "kind": kind,
                }
                scene = build_manifest("job", payload, "now")["storyboard"]["scenes"][0]
                self.assertEqual((scene["widthTarget"], scene["heightTarget"]), (width, height))
                self.assertEqual(scene["frameRateTarget"], fps)


if __name__ == "__main__":
    unittest.main()
