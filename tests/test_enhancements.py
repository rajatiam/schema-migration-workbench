import unittest, json, csv, io
from tests import test_migrations as fixtures
from schema_migration_workbench.core import apply, backup, status


class FeatureTests(unittest.TestCase):
    setUp = fixtures.MigrationTests.setUp
    tearDown = fixtures.MigrationTests.tearDown

    def test_backup_is_readable_and_source_unchanged(self):
        apply(self.db, self.directory)
        before = self.db.read_bytes()
        target = self.root / "backup.db"
        backup(self.db, target)
        self.assertEqual(status(target), status(self.db))
        self.assertEqual(before, self.db.read_bytes())

    def test_backup_does_not_overwrite(self):
        apply(self.db, self.directory)
        target = self.root / "backup.db"
        target.write_bytes(b"preserve")
        with self.assertRaises(ValueError):
            backup(self.db, target)
        self.assertEqual(target.read_bytes(), b"preserve")

    def test_missing_source_rejected(self):
        with self.assertRaises(ValueError):
            backup(self.db, self.root / "backup.db")
        self.assertFalse((self.root / "backup.db").exists())
