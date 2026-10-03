# Schema Migration Workbench: architecture

## Immutable history and transaction ownership

Migration names provide numeric ordering; SHA-256 checksums detect drift. The runner owns transactions and rejects embedded transaction or database-attachment commands. Dry runs copy the existing database into memory and execute pending SQL without changing the original.

## Module boundaries

`schema_migration_workbench/core.py` contains the algorithm and persistence operations. `cli.py` validates arguments and prints JSON. The package entrypoint translates input and storage errors into structured stderr with exit status 2. Domain-specific unsuccessful results can use exit status 1. There is no shared runtime dependency on the portfolio folder.

## Failure and operational boundaries

Each migration commits separately. If a later migration fails, earlier successful migrations remain applied and the failed migration rolls back. Removed or modified applied files and retroactive versions are rejected. Back up the database before schema changes; destructive SQL is allowed when explicitly authored in a migration.

## Verification

Core tests cover valid results and failure boundaries. Process-level CLI tests run the committed examples in temporary copies, inspect JSON output and verify domain outcomes. CI runs on Python 3.11 and 3.13, Linux and Windows, checks package installation, and builds and executes the non-root Docker image.

## Extension choices

The standard-library implementation keeps local execution inspectable and offline. A hosted or distributed version would require workload-specific authorization, resource limits, durable coordination and observability. Extend the core through tested functions rather than adding infrastructure without a scaling requirement.
