"""Transactional SQLite migrations, checksum drift detection and dry runs."""

__version__ = "1.0.0"


def entrypoint():
    import json, sqlite3, sys
    from .cli import main

    try:
        main()
    except (ValueError, OSError, sqlite3.Error, KeyError, TypeError) as exc:
        print(
            json.dumps({"error": str(exc), "type": type(exc).__name__}), file=sys.stderr
        )
        sys.exit(2)
