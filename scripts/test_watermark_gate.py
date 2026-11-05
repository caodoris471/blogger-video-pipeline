"""Offline behavioral checks; all media and review records are synthetic fixtures."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_watermark_free as gate


class DeliveryGateTests(unittest.TestCase):
    def setUp(self):
        # Caller sets TMP/TEMP to a project on the media drive, not the Skill folder.
        self.temp = tempfile.TemporaryDirectory(prefix="watermark-gate-")
        self.root = Path(self.temp.name)
        self.staging = self.root / gate.STAGING
        self.staging.mkdir(parents=True)
        self.video = self.staging / "001-synthetic.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                        "color=c=blue:s=32x32:d=0.2", "-c:v", "libx264", str(self.video)],
                       check=True, capture_output=True)
        gate.initialize(self.root, 1, "tiktok")

    def tearDown(self):
        self.temp.cleanup()

    def write(self, report):
        (self.root / gate.REPORT).write_text(json.dumps(report), encoding="utf-8")

    def reviewed(self):
        report = gate.load_report(self.root)
        item = report["videos"][0]
        evidence = self.root / "synthetic-review.md"
        evidence.write_text("Synthetic fixture review, not a real download.\n" + item["sha256"], encoding="utf-8")
        item.update(source_url="https://www.tiktok.com/@fixture/video/123", provider="synthetic",
                    watermark_status="clean", full_video_reviewed=True, reviewer="test fixture",
                    review_notes="Synthetic test fixture only", evidence=evidence.name)
        self.write(report)
        return report

    def test_pending_blocks_promotion(self):
        with self.assertRaises(ValueError):
            gate.promote(self.root)
        self.assertFalse((self.root / gate.DELIVERY / self.video.name).exists())

    def test_reviewed_fixture_promotes_and_changed_file_fails(self):
        self.reviewed()
        gate.promote(self.root)
        delivered = self.root / gate.DELIVERY / self.video.name
        self.assertEqual(gate.digest(delivered), gate.digest(self.video))
        self.assertTrue(gate.require_clean(self.root, expected_count=1))
        delivered.write_bytes(b"replaced after review")
        self.assertFalse(gate.require_clean(self.root))

    def test_uncertain_watermarked_and_sample_only_block(self):
        report = self.reviewed()
        for status in ("pending", "uncertain", "watermarked"):
            with self.subTest(status=status):
                changed = copy.deepcopy(report)
                changed["videos"][0]["watermark_status"] = status
                self.write(changed)
                with self.assertRaises(ValueError):
                    gate.validate(self.root, staging=True)
        report["videos"][0]["full_video_reviewed"] = False
        self.write(report)
        with self.assertRaises(ValueError):
            gate.validate(self.root, staging=True)

    def test_known_watermarked_formats_block(self):
        report = self.reviewed()
        for format_id, note in (("download", ""), ("download_addr", ""),
                                ("play", "Download video, watermarked")):
            with self.subTest(format_id=format_id, note=note):
                report["videos"][0].update(format_id=format_id, format_note=note)
                self.write(report)
                with self.assertRaises(ValueError):
                    gate.validate(self.root, staging=True)

    def test_missing_extra_duplicate_and_wrong_total_block(self):
        report = self.reviewed()
        for change in ("missing", "extra", "duplicate", "wrong_total", "zero"):
            with self.subTest(change=change):
                changed = copy.deepcopy(report)
                if change == "missing":
                    changed["videos"][0]["filename"] = "missing.mp4"
                elif change == "extra":
                    changed["videos"].append(dict(changed["videos"][0], filename="extra.mp4"))
                elif change == "duplicate":
                    changed["videos"].append(changed["videos"][0])
                elif change == "wrong_total":
                    changed["expected_count"] = 2
                else:
                    changed["expected_count"] = 0
                self.write(changed)
                with self.assertRaises(ValueError):
                    gate.validate(self.root, staging=True)

    def test_missing_or_unrelated_evidence_blocks(self):
        report = self.reviewed()
        for evidence in ("missing.md", "../outside.md"):
            report["videos"][0]["evidence"] = evidence
            self.write(report)
            with self.assertRaises(ValueError):
                gate.validate(self.root, staging=True)

    def test_new_content_resets_old_review(self):
        self.reviewed()
        self.video.write_bytes(b"new candidate")
        gate.initialize(self.root, 1, "tiktok")
        item = gate.load_report(self.root)["videos"][0]
        self.assertEqual(item["watermark_status"], "pending")
        self.assertFalse(item["full_video_reviewed"])

    def test_corrupt_candidate_cannot_pass_with_approved_record(self):
        self.video.write_bytes(b"not video")
        gate.initialize(self.root, 1, "tiktok")
        self.reviewed()
        with self.assertRaises(subprocess.CalledProcessError):
            gate.validate(self.root, staging=True)

    def test_all_collectors_target_staging(self):
        import importlib.util
        for script in Path(__file__).parent.glob("collect_videos_*.py"):
            spec = importlib.util.spec_from_file_location(script.stem, script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            destination = getattr(module, "TARGET_DIR", getattr(module, "SRC_DIR", None))
            self.assertEqual(destination.relative_to(module.BASE_DIR), gate.STAGING)

    def test_wx_does_not_transcribe_before_review(self):
        import wx_pipeline
        argv = ["wx_pipeline.py", "--nickname", "fixture", "--project", str(self.root), "--all"]
        with patch("sys.argv", argv), patch.object(wx_pipeline, "step_harvest", return_value=[{}]), \
                patch.object(wx_pipeline, "step_download", return_value=1) as download, \
                patch.object(wx_pipeline, "step_transcribe") as transcribe:
            self.assertEqual(wx_pipeline.main(), 2)
            self.assertEqual(download.call_args.args[1], self.staging)
            transcribe.assert_not_called()

    def test_tiktok_filter_keeps_playback_and_rejects_watermark_fallback(self):
        try:
            from yt_dlp import YoutubeDL
        except ImportError:
            self.skipTest("Optional yt-dlp is not installed")
        expression = ("best[ext=mp4][format_id!*=download][format_note!*=?watermarked]/"
                      "best[format_id!*=download][format_note!*=?watermarked]")
        clean = dict(format_id="play", url="https://example.com/p.mp4", ext="mp4",
                     vcodec="h264", acodec="aac")
        marked = dict(format_id="download", format_note="watermarked",
                      url="https://example.com/d.mp4", ext="mp4", vcodec="h264", acodec="aac")
        with YoutubeDL({"quiet": True}) as downloader:
            selector = downloader.build_format_selector(expression)
            def choose(formats):
                return [f["format_id"] for f in selector({
                    "formats": formats, "has_merged_format": True, "incomplete_formats": False})]
            self.assertEqual(choose([clean, marked]), ["play"])
            self.assertEqual(choose([clean]), ["play"])
            self.assertEqual(choose([marked]), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
