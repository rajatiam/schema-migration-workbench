# Schema Migration Workbench

Transactional SQLite migrations, checksum drift detection and dry runs. An independent Python 3.11+ project using the standard library, with a real command-line interface and no runtime package dependencies.

## Run locally

From the cloned repository, run:

```sh
python -m schema_migration_workbench plan examples/app.db examples/migrations
python -m schema_migration_workbench apply examples/app.db examples/migrations
python -m schema_migration_workbench status examples/app.db
```

Examples contain synthetic data. First use requires no cloud account, API key or package download. Optionally install the CLI using `python -m pip install .` and run `schema-migration-workbench --help`.

## Verify

```sh
python -m unittest discover -v
```

GitHub Actions checks Python 3.11 and 3.13 on Linux and Windows, verifies package installation, and builds/runs the non-root Docker image.

```sh
docker build -t schema-migration-workbench .
docker run --rm schema-migration-workbench --help
```

Mount a working directory at `/workspace` to process your own files. The container runs as UID 10001; provide appropriate write permissions for outputs.

## Architecture and scope

Business algorithms live in `schema_migration_workbench/core.py`; `schema_migration_workbench/cli.py` owns argument parsing and JSON output. Tests exercise success cases and failure boundaries, with temporary storage for mutations. See [design decisions](docs/architecture.md).

Migration files must be immutable once applied. Each numbered SQL file runs in a transaction. Explicit transaction statements, VACUUM and ATTACH are rejected. This is SQLite tooling, not a cross-database migration framework.

This project demonstrates implemented engineering practices. It does not claim production deployment history or external certifications.
