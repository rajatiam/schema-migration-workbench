"""Exercise the shipped examples through the real process entrypoint."""

import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def test_help_entrypoint(self):
        result = subprocess.run(
            [sys.executable, "-m", "schema_migration_workbench", "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout)

    def test_documented_workflow(self):
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder)
            shutil.copytree(
                ROOT / "schema_migration_workbench",
                clone / "schema_migration_workbench",
            )
            shutil.copytree(ROOT / "examples", clone / "examples")
            for command in [
                "plan examples/app.db examples/migrations",
                "apply examples/app.db examples/migrations",
                "status examples/app.db",
            ]:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "schema_migration_workbench",
                        *command.split(),
                    ],
                    cwd=clone,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
            self.assertEqual(len(payload["applied"]), 2)
