"""Local loudness processing and explicit pause-policy behavior; no paid calls."""
import array
import contextlib
import importlib.util
import io
import math
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("voice_audio", ROOT / "plugins/marketing-creative/skills/motion-voice/scripts/voice.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)
P = V.P


class VoiceAudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        P.init(self.root, "audio", ["16:9"], 8)
        self.rate = 44100
        self.data = array.array("h", (round(1400 * math.sin(2 * math.pi * 440 * i / self.rate))
                                      for i in range(4 * self.rate)))
        self.words = [{"id": f"w{i}", "segment": "line", "text": word, "start": .2 + .8 * i, "end": .5 + .8 * i}
                      for i, word in enumerate(["One", "two", "three", "four"])]
        self.script = {"schemaVersion": 1, "segments": [{"id": "line", "text": "One two three four"}]}
        P.write(self.root / "script.json", self.script)

    def save(self, data=None):
        V.commit(self.root, self.data if data is None else data, self.rate, {"words": self.words},
                 self.script, P.read(self.root / "project.json"))

    def run_voice(self, *args):
        with mock.patch.object(sys, "argv", ["voice.py", args[0], str(self.root), *args[1:]]), contextlib.redirect_stdout(io.StringIO()) as output:
            V.main()
        return output.getvalue()

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def silent_gaps(self):
        data = array.array("h", [0]) * len(self.data)
        for word in self.words:
            a, b = round(word["start"] * self.rate), round(word["end"] * self.rate)
            data[a:b] = self.data[a:b]
        return data

    def config(self, value):
        path = Path(self.temp.name) / "pause.json"
        P.write(path, value)
        return str(path)

    def voice_config(self):
        path = Path(self.temp.name) / "voice.json"
        P.write(path, {"voiceId": "selected", "modelId": "selected", "language": "en", "voiceSettings": {}})
        return str(path)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for measured loudness")
    def test_normalize_meets_targets_preserves_clock_and_backs_up(self):
        self.save()
        P.resolve(self.root)
        before = P.read(self.root / "audio/alignment.json")
        original = (self.root / "audio/vo.wav").read_bytes()
        self.run_voice("normalize")
        after = P.read(self.root / "audio/alignment.json")
        data, rate = V.pcm_read(self.root / "audio/vo.wav")
        self.assertEqual((len(data), rate), (len(self.data), self.rate))
        self.assertEqual(before["words"], after["words"])
        self.assertNotEqual(before["audioSha256"], after["audioSha256"])
        self.assertEqual(after["loudness"]["audioSha256"], after["audioSha256"])
        self.assertAlmostEqual(after["loudness"]["measured"]["integrated"], -16, delta=.5)
        self.assertLessEqual(after["loudness"]["measured"]["truePeak"], -1.3)
        self.assertTrue(any(p.read_bytes() == original for p in (self.root / "audio/backups").glob("*/vo.wav")))
        self.assertFalse((self.root / "timing.resolved.json").exists())
        P.validate_alignment(self.root, P.read(self.root / "project.json"), self.script)

    def test_normalize_dry_run_does_not_process_or_write(self):
        self.save()
        before = self.snapshot()
        with mock.patch.object(V, "normalize_take", side_effect=AssertionError("processing in dry-run")):
            self.run_voice("normalize", "--dry-run")
        self.assertEqual(self.snapshot(), before)

    def test_invalid_targets_fail_without_mutation(self):
        self.save()
        before = self.snapshot()
        for flag, value in (("--target-lufs", "nan"), ("--target-lufs", "-4"), ("--true-peak", "1"), ("--lra", "0")):
            with self.subTest(flag=flag, value=value), self.assertRaises(ValueError):
                self.run_voice("normalize", flag, value)
            self.assertEqual(self.snapshot(), before)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for silence measurement")
    def test_unmeasurable_silence_preserves_project(self):
        self.save(array.array("h", [0]) * len(self.data))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "no measurable loudness"):
            self.run_voice("normalize")
        self.assertEqual(self.snapshot(), before)

    def test_normalize_refuses_changed_sample_clock(self):
        self.save()
        before = self.snapshot()
        def fake_run(source, options, output=None, rate=44100):
            if output:
                V.pcm_write(output, self.data[:-1], rate)
            return {"input_i": "-25", "input_tp": "-20", "input_lra": "0", "input_thresh": "-35", "target_offset": "0"}
        with mock.patch.object(V, "loudnorm_run", side_effect=fake_run), self.assertRaisesRegex(ValueError, "frame count"):
            self.run_voice("normalize")
        self.assertEqual(self.snapshot(), before)

    def test_failed_generated_normalization_keeps_paid_take(self):
        config = self.voice_config()
        with mock.patch.object(V, "provider_take", return_value=(self.data, self.rate, {"words": self.words})) as provider, \
             mock.patch.object(V, "normalize_take", side_effect=ValueError("local normalization failed")), \
             mock.patch.object(V.shutil, "which", return_value="ffmpeg"), \
             self.assertRaisesRegex(ValueError, "local normalization failed"):
            self.run_voice("generate", "--config", config)
        provider.assert_called_once()
        project = P.read(self.root / "project.json")
        P.validate_alignment(self.root, project, self.script)
        self.assertEqual(V.pcm_read(self.root / "audio/vo.wav")[0], self.data)
        with self.assertRaisesRegex(ValueError, "Existing take"):
            self.run_voice("generate", "--config", config)

    def test_generate_can_preserve_source_level(self):
        with mock.patch.object(V, "provider_take", return_value=(self.data, self.rate, {"words": self.words})), \
             mock.patch.object(V, "normalize_take", side_effect=AssertionError("unexpected normalization")), \
             mock.patch.object(V.shutil, "which", return_value="ffmpeg"):
            self.run_voice("generate", "--config", self.voice_config(), "--no-normalize")
        self.assertEqual(V.pcm_read(self.root / "audio/vo.wav")[0], self.data)
        self.assertNotIn("loudness", P.read(self.root / "audio/alignment.json"))

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for import conversion")
    def test_import_preserves_level_unless_requested(self):
        source = Path(self.temp.name) / "source.wav"
        alignment = Path(self.temp.name) / "alignment.json"
        V.pcm_write(source, self.data, self.rate)
        P.write(alignment, {"words": self.words})
        self.run_voice("import", "--audio", str(source), "--alignment", str(alignment))
        self.assertEqual(V.pcm_read(self.root / "audio/vo.wav")[0], self.data)
        self.run_voice("import", "--audio", str(source), "--alignment", str(alignment), "--normalize", "--target-lufs", "-20")
        result = P.read(self.root / "audio/alignment.json")
        self.assertAlmostEqual(result["loudness"]["measured"]["integrated"], -20, delta=.5)

    def test_pause_classes_retime_exactly_and_preserve_dramatic_pause(self):
        self.save(self.silent_gaps())
        config = self.config({"schemaVersion": 1, "classes": {"default": .24, "step": .42, "dramatic": None}, "rules": [
            {"before": {"segment": "line", "quote": "two"}, "class": "step"},
            {"before": {"segment": "line", "quote": "three"}, "class": "dramatic"}]})
        before = self.snapshot()
        self.run_voice("trim", "--pause-config", config, "--dry-run")
        self.assertEqual(before, self.snapshot())
        self.run_voice("trim", "--pause-config", config)
        after = P.read(self.root / "audio/alignment.json")
        data, _ = V.pcm_read(self.root / "audio/vo.wav")
        self.assertEqual(len(self.data) - len(data), round(.34 * self.rate))
        words = after["words"]
        self.assertAlmostEqual(words[1]["start"] - words[0]["end"], .42)
        self.assertAlmostEqual(words[2]["start"] - words[1]["end"], .5)
        self.assertAlmostEqual(words[3]["start"] - words[2]["end"], .24)
        P.validate_alignment(self.root, P.read(self.root / "project.json"), self.script)

    def test_invalid_pause_rules_do_not_change_take(self):
        self.save(self.silent_gaps())
        before = self.snapshot()
        rule = {"before": {"segment": "line", "quote": "two"}, "class": "step"}
        configs = [
            {"schemaVersion": 1, "classes": {"step": .42}},
            {"schemaVersion": 1, "classes": {"default": -.1}},
            {"schemaVersion": 1, "classes": {"default": True}},
            {"schemaVersion": 1, "classes": {"default": .24}, "rules": [rule]},
            {"schemaVersion": 1, "classes": {"default": .24, "step": .42}, "rules": [rule, rule]},
            {"schemaVersion": 1, "classes": {"default": .24}, "rules": [{"before": {"segment": "line", "quote": "missing"}, "class": "default"}]},
            {"schemaVersion": 1, "classes": {"default": .24}, "rules": [{"before": {"segment": "line", "quote": "One"}, "class": "default"}]},
        ]
        for config in configs:
            with self.subTest(config=config), self.assertRaises(ValueError):
                self.run_voice("trim", "--pause-config", self.config(config))
            self.assertEqual(before, self.snapshot())

    def test_pause_cues_support_unicode_and_explicit_occurrence(self):
        words = [{"segment": "a", "text": t} for t in ("开始", "你好", "世界", "你好")]
        config = {"schemaVersion": 1, "classes": {"default": .24, "hold": None}, "rules": [
            {"before": {"segment": "a", "quote": "你好", "occurrence": 2}, "class": "hold"}]}
        self.assertEqual(V.pause_policy(words, .24, config), [("default", .24), ("default", .24), ("hold", None)])
        del config["rules"][0]["before"]["occurrence"]
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            V.pause_policy(words, .24, config)

    def test_pcm_edit_discards_stale_loudness_report(self):
        self.save(self.silent_gaps())
        alignment = P.read(self.root / "audio/alignment.json")
        alignment["loudness"] = {"audioSha256": alignment["audioSha256"], "measured": {"integrated": -16}}
        P.write(self.root / "audio/alignment.json", alignment)
        self.run_voice("trim")
        self.assertNotIn("loudness", P.read(self.root / "audio/alignment.json"))


if __name__ == "__main__":
    unittest.main()
