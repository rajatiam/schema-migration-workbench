"""Immutable checksummed SQLite migration plans and transactional execution."""

from pathlib import Path
import hashlib, re, sqlite3


def files(directory):
    result = []
    versions = set()
    for file in sorted(Path(directory).glob("*.sql")):
        match = re.fullmatch(r"(\d+)_([A-Za-z0-9_-]+)\.sql", file.name)
        if not match:
            raise ValueError("Use numbered migration_name.sql files")
        version = int(match[1])
        if version in versions or version < 1:
            raise ValueError("Duplicate or invalid migration version")
        versions.add(version)
        text = file.read_text(encoding="utf-8")
        if re.search(
            r"\b(BEGIN|COMMIT|ROLLBACK|VACUUM|ATTACH|DETACH|PRAGMA)\b", text, re.I
        ):
            raise ValueError(
                "Transaction, database attachment and pragma commands are not allowed"
            )
        result.append(
            {
                "version": version,
                "name": file.name,
                "checksum": hashlib.sha256(text.encode()).hexdigest(),
                "sql": text,
            }
        )
    result.sort(key=lambda row: row["version"])
    if not result:
        raise ValueError("No migration files")
    return result


def statements(text):
    buffer = ""
    for character in text:
        buffer += character
        if character == ";" and sqlite3.complete_statement(buffer):
            yield buffer
            buffer = ""
    if buffer.strip():
        if sqlite3.complete_statement(buffer + ";"):
            yield buffer
        else:
            raise ValueError("Incomplete SQL statement")


def history(connection):
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='_migrations'"
    ).fetchone()
    if not exists:
        return []
    return [
        dict(zip(["version", "name", "checksum"], row))
        for row in connection.execute(
            "SELECT version,name,checksum FROM _migrations ORDER BY version"
        )
    ]


def pending(connection, migrations):
    applied = history(connection)
    lookup = {row["version"]: row for row in migrations}
    for row in applied:
        candidate = lookup.get(row["version"])
        if not candidate or any(
            row[key] != candidate[key] for key in ["name", "checksum"]
        ):
            raise ValueError("Applied migration is missing or has checksum drift")
    latest = max((row["version"] for row in applied), default=0)
    if any(
        row["version"] <= latest
        and row["version"] not in {r["version"] for r in applied}
        for row in migrations
    ):
        raise ValueError("Cannot insert a migration before applied history")
    return [row for row in migrations if row["version"] > latest]


def execute(connection, migrations):
    connection.execute(
        "CREATE TABLE IF NOT EXISTS _migrations(version INTEGER PRIMARY KEY,name TEXT NOT NULL,checksum TEXT NOT NULL)"
    )
    for row in migrations:
        for statement in statements(row["sql"]):
            connection.execute(statement)
        connection.execute(
            "INSERT INTO _migrations VALUES (?,?,?)",
            (row["version"], row["name"], row["checksum"]),
        )


def plan(database, directory):
    migrations = files(directory)
    source = None
    memory = sqlite3.connect(":memory:")
    try:
        if Path(database).exists():
            source = sqlite3.connect(
                Path(database).resolve().as_uri() + "?mode=ro", uri=True
            )
            source.backup(memory)
        memory.execute("PRAGMA foreign_keys=ON")
        todo = pending(memory, migrations)
        memory.execute("BEGIN")
        execute(memory, todo)
        memory.rollback()
        return {
            "pending": [{k: v for k, v in row.items() if k != "sql"} for row in todo],
            "dry_run": True,
        }
    finally:
        memory.close()
        if source:
            source.close()


def apply(database, directory):
    migrations = files(directory)
    connection = sqlite3.connect(database, timeout=15)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        applied = []
        for migration in migrations:
            connection.execute("BEGIN IMMEDIATE")
            try:
                todo = pending(connection, migrations)
                if migration in todo:
                    execute(connection, [migration])
                    applied.append(migration["name"])
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
        return {"applied": applied}
    finally:
        connection.close()


def status(database):
    if not Path(database).exists():
        return {"applied": []}
    connection = sqlite3.connect(
        Path(database).resolve().as_uri() + "?mode=ro", uri=True
    )
    try:
        return {"applied": history(connection)}
    finally:
        connection.close()


def backup(database, target):
    import os, tempfile

    source = Path(database).resolve()
    target = Path(target).absolute()
    if not source.is_file():
        raise ValueError("Source database does not exist")
    if source == target.resolve() or target.exists():
        raise ValueError("Backup target must be new and separate from source")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        temporary = Path(stream.name)
    origin = destination = None
    try:
        origin = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
        destination = sqlite3.connect(temporary)
        origin.backup(destination)
        destination.close()
        destination = None
        origin.close()
        origin = None
        os.link(temporary, target)
        return {"backup": str(target), "bytes": target.stat().st_size}
    finally:
        if origin:
            origin.close()
        if destination:
            destination.close()
        temporary.unlink(missing_ok=True)
