import sqlite3, tempfile, unittest
from pathlib import Path
from schema_migration_workbench.core import apply, plan, status


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.directory = self.root / "migrations"
        self.directory.mkdir()
        self.db = self.root / "app.db"
        (self.directory / "001_users.sql").write_text(
            "CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);"
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_apply_once(self):
        self.assertEqual(len(apply(self.db, self.directory)["applied"]), 1)
        self.assertEqual(apply(self.db, self.directory)["applied"], [])

    def test_plan_does_not_create_database(self):
        self.assertEqual(len(plan(self.db, self.directory)["pending"]), 1)
        self.assertFalse(self.db.exists())

    def test_invalid_migration_rolls_back(self):
        (self.directory / "001_users.sql").write_text(
            "CREATE TABLE users(id INTEGER);INSERT INTO missing VALUES (1);"
        )
        with self.assertRaises(sqlite3.Error):
            apply(self.db, self.directory)
        connection = sqlite3.connect(self.db)
        try:
            self.assertIsNone(
                connection.execute(
                    "SELECT name FROM sqlite_master WHERE name='users'"
                ).fetchone()
            )
        finally:
            connection.close()

    def test_checksum_drift_detected(self):
        apply(self.db, self.directory)
        (self.directory / "001_users.sql").write_text(
            "CREATE TABLE users(changed TEXT);"
        )
        with self.assertRaises(ValueError):
            plan(self.db, self.directory)

    def test_missing_applied_file_detected(self):
        apply(self.db, self.directory)
        (self.directory / "001_users.sql").unlink()
        (self.directory / "002_new.sql").write_text("CREATE TABLE other(id INTEGER);")
        with self.assertRaises(ValueError):
            apply(self.db, self.directory)

    def test_semicolon_in_string(self):
        (self.directory / "001_users.sql").write_text(
            "CREATE TABLE users(name TEXT);INSERT INTO users VALUES ('a;b');"
        )
        apply(self.db, self.directory)
        self.assertEqual(len(status(self.db)["applied"]), 1)

    def test_existing_database_unchanged_by_plan(self):
        apply(self.db, self.directory)
        before = self.db.read_bytes()
        (self.directory / "002_other.sql").write_text("CREATE TABLE other(id INTEGER);")
        plan(self.db, self.directory)
        self.assertEqual(before, self.db.read_bytes())
