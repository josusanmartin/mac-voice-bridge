import contextlib
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/mac-voice-bridge/scripts"))
import audio_state
import offline_check


class FakeAudio:
    """Invented metadata; cannot load a framework or open real devices."""
    def __init__(self):
        self.devices = [{"id": 11, "uid": "test-input", "name": "Fixture input"},
                        {"id": 12, "uid": "test-output", "name": "Fixture output"},
                        {"id": 13, "uid": "test-bus-a", "name": "Fixture bus A"},
                        {"id": 14, "uid": "test-bus-b", "name": "Fixture bus B"}]
        self.defaults = {"input": 11, "output": 12, "alerts": 12}
        self.calls, self.fail, self.ignore = [], set(), set()

    def inventory(self):
        return copy.deepcopy({"devices": self.devices, "defaults": self.defaults})

    def set_default(self, key, device):
        self.calls.append((key, device))
        if key in self.fail:
            raise RuntimeError(f"Simulated failure: {key}")
        if key not in self.ignore:
            self.defaults[key] = device

    def bridge(self):
        self.defaults.update(input=14, output=13)


class DetectorTests(unittest.TestCase):
    def test_fault_controls(self):
        self.assertTrue(all(offline_check.check().values()))

    def test_threshold_accepts_small_leakage(self):
        a, b = offline_check.tone(440), offline_check.tone(880)
        leaking = [x + 0.001 * y for x, y in zip(a, b)]
        self.assertTrue(offline_check.valid_routes(leaking, b))

    def test_near_silence_rejected(self):
        self.assertFalse(offline_check.valid_routes(offline_check.tone(440, 0.001), offline_check.tone(880, 0.001)))


class RestorationTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeAudio()
        self.saved = audio_state.make_snapshot(self.backend)
        self.backend.bridge()

    def test_preview_never_mutates(self):
        before = self.backend.inventory()
        result = audio_state.restore(self.backend, self.saved)
        self.assertEqual(result["changes"], ["input", "output"])
        self.assertFalse(result["restored"])
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.backend.inventory(), before)

    def test_restore_uses_current_ids(self):
        for device in self.backend.devices:
            device["id"] += 100
        self.backend.defaults = {key: value + 100 for key, value in self.backend.defaults.items()}
        result = audio_state.restore(self.backend, self.saved, apply=True)
        self.assertTrue(result["restored"])
        self.assertEqual(self.backend.calls, [("input", 111), ("output", 112)])

    def test_already_restored_is_idempotent(self):
        audio_state.restore(self.backend, self.saved, apply=True)
        self.backend.calls.clear()
        result = audio_state.restore(self.backend, self.saved, apply=True)
        self.assertTrue(result["restored"])
        self.assertEqual(self.backend.calls, [])

    def test_missing_device_restores_other_paths(self):
        self.backend.devices = [device for device in self.backend.devices if device["uid"] != "test-input"]
        result = audio_state.restore(self.backend, self.saved, apply=True)
        self.assertFalse(result["restored"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(self.backend.calls, [("output", 12)])

    def test_duplicate_uid_refused(self):
        self.backend.devices.append({"id": 15, "uid": "test-input", "name": "Duplicate fixture"})
        result = audio_state.restore(self.backend, self.saved, apply=True)
        self.assertFalse(result["restored"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertNotIn(("input", 11), self.backend.calls)

    def test_write_failure_does_not_stop_other_paths(self):
        self.backend.fail.add("input")
        result = audio_state.restore(self.backend, self.saved, apply=True)
        self.assertFalse(result["restored"])
        self.assertEqual(result["errors"], ["Simulated failure: input"])
        self.assertEqual(self.backend.defaults["output"], 12)

    def test_readback_detects_ignored_write(self):
        self.backend.ignore.add("output")
        result = audio_state.restore(self.backend, self.saved, apply=True)
        self.assertFalse(result["restored"])

    def test_alert_output_restored_too(self):
        self.backend.defaults["alerts"] = 13
        result = audio_state.restore(self.backend, self.saved, apply=True)
        self.assertTrue(result["restored"])
        self.assertIn(("alerts", 12), self.backend.calls)

    def test_invalid_snapshot_never_mutates(self):
        for malformed in ({}, {"version": 2, "defaults": self.saved["defaults"]},
                          {"version": 1, "defaults": {"input": "test-input"}},
                          {"version": 1, "defaults": {"input": [], "output": "a", "alerts": "b"}},
                          []):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                audio_state.restore(self.backend, malformed, apply=True)
        self.assertEqual(self.backend.calls, [])


class FileAndCliTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeAudio()
        self.saved = audio_state.make_snapshot(self.backend)
        self.backend.bridge()

    def invoke(self, args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return audio_state.main(args, backend_factory=lambda: self.backend)

    def test_snapshot_exclusive_and_private(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "baseline.json"
            audio_state.write_snapshot(path, self.saved)
            if os.name == "posix":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                audio_state.write_snapshot(path, self.saved)
            self.assertEqual(json.loads(path.read_text()), self.saved)

    @unittest.skipUnless(os.name == "posix", "Symlink permission behavior is POSIX")
    def test_snapshot_does_not_follow_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "target.txt"
            target.write_text("keep")
            path = Path(folder) / "baseline.json"
            path.symlink_to(target)
            with self.assertRaises(FileExistsError):
                audio_state.write_snapshot(path, self.saved)
            self.assertEqual(target.read_text(), "keep")

    def test_apply_requires_call_state_before_backend(self):
        constructed = []
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            audio_state.main(["restore", "unused.json", "--apply"], backend_factory=lambda: constructed.append(True))
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(constructed, [])

    def test_invalid_file_rejected_before_backend(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text("[]")
            constructed = []
            with contextlib.redirect_stderr(io.StringIO()):
                code = audio_state.main(["restore", str(path), "--apply", "--call-ended"], backend_factory=lambda: constructed.append(True))
            self.assertEqual(code, 1)
            self.assertEqual(constructed, [])

    def test_cli_preview_and_apply(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "baseline.json"
            audio_state.write_snapshot(path, self.saved)
            self.assertEqual(self.invoke(["restore", str(path)]), 0)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.invoke(["restore", str(path), "--apply", "--call-ended"]), 0)
            self.assertEqual(audio_state.make_snapshot(self.backend), self.saved)

    def test_emergency_path_and_readback_failure_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "baseline.json"
            audio_state.write_snapshot(path, self.saved)
            self.backend.ignore.add("input")
            self.assertEqual(self.invoke(["restore", str(path), "--apply", "--emergency"]), 1)

    def test_missing_file_has_no_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(self.invoke(["restore", str(Path(folder) / "missing.json"), "--apply", "--call-ended"]), 1)
            self.assertEqual(self.backend.calls, [])


if __name__ == "__main__":
    unittest.main()
