import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".agents/skills/submitting-upstream"
SCRIPT = SKILL_DIR / "scripts/paste-form-fields.sh"
REFERENCE = SKILL_DIR / "reference/manual-web-form-submission.md"

# Stubs log each call so the test can assert order, delays and clipboard bytes
# without touching the real clipboard, notification daemon or wall clock.
STUBS = {
    "notify-send": 'printf "notify %s\\n" "$*" >> "$STUB_LOG"\n',
    "sleep": 'printf "sleep %s\\n" "$1" >> "$STUB_LOG"\n',
    "xclip": (
        'if [ "$3" = -o ]; then\n'
        '    if [ -n "${STUB_CORRUPT:-}" ]; then printf stale; else cat "$STUB_CLIP"; fi\n'
        "else\n"
        '    cat > "$STUB_CLIP"\n'
        '    cp "$STUB_CLIP" "$STUB_CLIP.$(ls "$STUB_CLIP".* 2>/dev/null | wc -l | tr -d " ")"\n'
        "fi\n"
    ),
}


class PasteFormFieldsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        for name, body in STUBS.items():
            stub = bin_dir / name
            stub.write_text("#!/bin/sh\n" + body)
            stub.chmod(0o755)
        self.log = self.tmp / "log"
        self.clip = self.tmp / "clip"
        self.env = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "DISPLAY": ":99",
            "STUB_LOG": str(self.log),
            "STUB_CLIP": str(self.clip),
        }
        self.env.pop("WAYLAND_DISPLAY", None)
        fields = self.tmp / "fields"
        fields.mkdir()
        (fields / "1-title.txt").write_text(
            "#NOTE: Select all first\n[Feature]: Example\n"
        )
        (fields / "2-problem-or-use-case.txt").write_text("Line one.\n\nLine two.\n")
        (fields / "3-proposed-solution.txt").write_text("Do the thing.\n")
        self.files = sorted(str(p) for p in fields.iterdir())

    def run_script(self, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(SCRIPT), *args, *self.files],
            env={**self.env, **env},
            capture_output=True,
            text=True,
        )

    def test_announces_each_field_in_order_with_default_delays(self) -> None:
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.log.read_text().splitlines(),
            [
                "notify -t 10000 Field 1/3 ready, next in 5s "
                "Paste into: Title — Select all first",
                "sleep 5",
                "notify -t 10000 Field 2/3 ready, next in 5s "
                "Paste into: Problem or use case",
                "sleep 5",
                "notify -t 10000 Field 3/3 ready (last) Paste into: Proposed solution",
            ],
        )

    def test_delay_options_override_defaults(self) -> None:
        result = self.run_script("-f", "8", "-d", "2", "-t", "4")
        self.assertEqual(result.returncode, 0, result.stderr)
        log = self.log.read_text()
        self.assertIn("sleep 8\n", log)
        self.assertIn("sleep 2\n", log)
        self.assertIn("notify -t 4000 ", log)

    def test_clipboard_gets_exact_content_without_note_or_trailing_newline(
        self,
    ) -> None:
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        copies = [self.clip.with_name(f"clip.{n}").read_bytes() for n in range(3)]
        self.assertEqual(
            copies,
            [b"[Feature]: Example", b"Line one.\n\nLine two.", b"Do the thing."],
        )

    def test_clipboard_mismatch_aborts_before_advancing(self) -> None:
        result = self.run_script(STUB_CORRUPT="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("clipboard mismatch", result.stderr)
        self.assertEqual(
            self.log.read_text().splitlines(),
            ["notify -t 10000 Paste aborted Clipboard check failed for Title"],
        )

    def test_reference_drives_the_script(self) -> None:
        text = REFERENCE.read_text()
        self.assertIn("scripts/paste-form-fields.sh", text)
        self.assertNotIn("One\nfield per turn", text)


if __name__ == "__main__":
    unittest.main()
