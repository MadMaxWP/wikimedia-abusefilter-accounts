import os
import sys
import tempfile
import types
import unittest
from pathlib import Path


class FakeDatabaseError(Exception):
    pass


class FakeCursor:
    def __init__(self, rows, fail=False):
        self.rows = rows
        self.fail = fail
        self.closed = False
        self.query = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.closed = True
        return False

    def execute(self, query):
        self.query = query
        if self.fail:
            raise RuntimeError("query failed")

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows, fail=False):
        self.cursor_obj = FakeCursor(rows, fail)
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def close(self):
        self.closed = True


class FakeToolforge:
    UnknownDatabaseError = FakeDatabaseError

    def __init__(self, databases):
        self.databases = databases
        self.connections = []
        self.calls = []
        self.dbname_calls = []
        self.fail = False

    def dbname(self, value):
        self.dbname_calls.append(value)
        if value in {"en.wikipedia.org", "https://en.wikipedia.org", "https://en.wikipedia.org/wiki/Main_Page"}:
            return "enwiki"
        raise FakeDatabaseError(value)

    def connect(self, dbname, **kwargs):
        if self.connections and not self.connections[-1].closed:
            raise AssertionError("previous connection was not closed")
        self.calls.append((dbname, kwargs))
        connection = FakeConnection(self.databases.get(dbname, []), self.fail)
        self.connections.append(connection)
        return connection


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeToolforge({"enwiki": [(b"Alice_Example",), ("Jean Dupont",), (b"Fran\xc3\xa7ois_Example",)], "dewiki": [(b"Bob_Smith",)]})
        module = types.ModuleType("toolforge")
        module.connect = self.fake.connect
        module.dbname = self.fake.dbname
        module.UnknownDatabaseError = self.fake.UnknownDatabaseError
        sys.modules["toolforge"] = module
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        sys.modules.pop("abusefilter_accounts", None)
        import abusefilter_accounts
        self.package = abusefilter_accounts

    def tearDown(self):
        sys.modules.pop("abusefilter_accounts", None)
        sys.modules.pop("toolforge", None)
        sys.path.pop(0)

    def test_version(self):
        self.assertEqual(self.package.__version__, "0.1.0")

    def test_single_db_decodes_and_replaces_underscores(self):
        self.assertEqual(self.package.get_abuse_filter_accounts("enwiki"), {"enwiki": ["Alice Example", "Jean Dupont", "Fran\u00e7ois Example"]})
        self.assertTrue(self.fake.connections[0].closed)
        self.assertTrue(self.fake.connections[0].cursor_obj.closed)

    def test_host_and_url_are_resolved(self):
        self.assertEqual(self.package.get_abuse_filter_accounts(["en.wikipedia.org", "https://en.wikipedia.org/wiki/Main_Page"]), {"enwiki": ["Alice Example", "Jean Dupont", "Fran\u00e7ois Example"]})
        self.assertEqual(self.fake.dbname_calls, ["en.wikipedia.org", "https://en.wikipedia.org/wiki/Main_Page"])
        self.assertEqual([call[0] for call in self.fake.calls], ["enwiki"])

    def test_multiple_wikis(self):
        self.assertEqual(self.package.get_abuse_filter_accounts(["enwiki", "dewiki"]), {"enwiki": ["Alice Example", "Jean Dupont", "Fran\u00e7ois Example"], "dewiki": ["Bob Smith"]})
        self.assertTrue(all(connection.closed for connection in self.fake.connections))
        self.assertTrue(all(connection.cursor_obj.closed for connection in self.fake.connections))

    def test_generator_wikis(self):
        self.assertEqual(self.package.get_abuse_filter_accounts(wiki for wiki in ["enwiki", "dewiki"]), {"enwiki": ["Alice Example", "Jean Dupont", "Fran\u00e7ois Example"], "dewiki": ["Bob Smith"]})

    def test_all_open_wikis_decodes_dbnames(self):
        self.fake.databases["meta_p"] = [(b"dewiki",), (b"enwiki",)]
        self.assertEqual(self.package.get_abuse_filter_accounts(), {"dewiki": ["Bob Smith"], "enwiki": ["Alice Example", "Jean Dupont", "Fran\u00e7ois Example"]})
        self.assertEqual([call[0] for call in self.fake.calls], ["meta_p", "dewiki", "enwiki"])
        self.assertTrue(all(connection.closed for connection in self.fake.connections))
        self.assertTrue(all(connection.cursor_obj.closed for connection in self.fake.connections))

    def test_query_contents(self):
        self.package.get_abuse_filter_accounts("enwiki")
        query = self.fake.connections[0].cursor_obj.query
        self.assertIn("ug_group = 'sysop'", query)
        self.assertIn("ug_expiry IS NULL", query)
        self.assertIn("UTC_TIMESTAMP()", query)
        self.assertIn("NOT EXISTS", query)
        self.assertIn("revision_userindex", query)
        self.assertIn("actor_user = u.user_id", query)

    def test_default_credentials_are_left_to_toolforge_when_missing(self):
        old_home = os.environ.get("HOME")
        with tempfile.TemporaryDirectory() as home:
            os.environ["HOME"] = home
            try:
                self.package.get_abuse_filter_accounts("enwiki")
            finally:
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home
        self.assertEqual(self.fake.calls[0][1], {})

    def test_custom_config_is_used(self):
        with tempfile.NamedTemporaryFile() as config:
            self.package.get_abuse_filter_accounts("enwiki", cnf_file=config.name)
        self.assertEqual(self.fake.calls[0][1], {"read_default_file": config.name})

    def test_pathlike_custom_config_is_used(self):
        with tempfile.NamedTemporaryFile() as config:
            self.package.get_abuse_filter_accounts("enwiki", cnf_file=Path(config.name))
        self.assertEqual(self.fake.calls[0][1], {"read_default_file": config.name})

    def test_missing_custom_config_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.package.get_abuse_filter_accounts("enwiki", cnf_file="/does/not/exist")
        self.assertEqual(self.fake.calls, [])

    def test_query_failure_still_closes_connection_and_cursor(self):
        self.fake.fail = True
        with self.assertRaises(RuntimeError):
            self.package.get_abuse_filter_accounts("enwiki")
        self.assertTrue(self.fake.connections[0].closed)
        self.assertTrue(self.fake.connections[0].cursor_obj.closed)

    def test_unknown_host_is_not_used_as_a_db_name(self):
        with self.assertRaises(FakeDatabaseError):
            self.package.get_abuse_filter_accounts("not-a-wiki.example.org")
        self.assertEqual(self.fake.calls, [])

    def test_bytes_wikis_is_rejected(self):
        with self.assertRaises(TypeError):
            self.package.get_abuse_filter_accounts(b"enwiki")
        self.assertEqual(self.fake.calls, [])

    def test_non_string_wiki_is_rejected(self):
        with self.assertRaises(TypeError):
            self.package.get_abuse_filter_accounts(["enwiki", 123])
        self.assertEqual(self.fake.calls, [])

    def test_empty_wiki_is_rejected(self):
        with self.assertRaises(ValueError):
            self.package.get_abuse_filter_accounts("   ")
        self.assertEqual(self.fake.calls, [])

    def test_whitespace_is_stripped(self):
        self.assertEqual(self.package.get_abuse_filter_accounts(" enwiki "), {"enwiki": ["Alice Example", "Jean Dupont", "Fran\u00e7ois Example"]})

    def test_duplicate_wikis_are_processed_once(self):
        self.assertEqual(self.package.get_abuse_filter_accounts(["enwiki", "enwiki", "en.wikipedia.org"]), {"enwiki": ["Alice Example", "Jean Dupont", "Fran\u00e7ois Example"]})
        self.assertEqual([call[0] for call in self.fake.calls], ["enwiki"])

    def test_replica_config_is_preferred(self):
        with tempfile.TemporaryDirectory() as home:
            pathlib_home = Path(home)
            (pathlib_home / "replica.my.cnf").write_text("[client]\n")
            (pathlib_home / ".my.cnf").write_text("[client]\n")
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = home
            try:
                self.package.get_abuse_filter_accounts("enwiki")
            finally:
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home
        self.assertEqual(self.fake.calls[0][1], {"read_default_file": str(pathlib_home / "replica.my.cnf")})

    def test_home_credential_fallback(self):
        with tempfile.TemporaryDirectory() as home:
            pathlib_home = Path(home)
            (pathlib_home / ".my.cnf").write_text("[client]\n")
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = home
            try:
                self.package.get_abuse_filter_accounts("enwiki")
            finally:
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home
        self.assertEqual(self.fake.calls[0][1], {"read_default_file": str(pathlib_home / ".my.cnf")})


if __name__ == "__main__":
    unittest.main()
