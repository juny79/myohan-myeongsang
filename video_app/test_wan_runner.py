"""Unit tests for Wan smoke-test command construction."""
import unittest
from pathlib import Path

from video_app.wan_smoke_test import build_command


class WanSmokeCommandTests(unittest.TestCase):
    def test_wan21_uses_only_supported_memory_flags(self):
        command = build_command(
            "local_preview", Path("Wan2.1"), Path("weights"), Path("out.mp4"), "quiet cat"
        )
        self.assertIn("t2v-1.3B", command)
        self.assertIn("--t5_cpu", command)
        self.assertIn("--offload_model", command)
        self.assertNotIn("--convert_model_dtype", command)
        self.assertIn("832*480", command)

    def test_wan22_ti2v_uses_offload_and_dtype_conversion(self):
        command = build_command(
            "standard_scene", Path("Wan2.2"), Path("weights"), Path("out.mp4"), "quiet cat"
        )
        self.assertIn("ti2v-5B", command)
        self.assertIn("--convert_model_dtype", command)
        self.assertIn("1280*704", command)
        self.assertNotIn("--image", command)

    def test_wan22_i2v_requires_and_uses_reference_image(self):
        with self.assertRaises(ValueError):
            build_command(
                "premium_scene", Path("Wan2.2"), Path("weights"), Path("out.mp4"), "quiet cat"
            )
        command = build_command(
            "premium_scene", Path("Wan2.2"), Path("weights"), Path("out.mp4"),
            "quiet cat", Path("reference.png")
        )
        self.assertIn("i2v-A14B", command)
        self.assertIn("--image", command)
        self.assertIn("--convert_model_dtype", command)
        self.assertIn("1280*720", command)


if __name__ == "__main__":
    unittest.main()
