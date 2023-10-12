# Usage Examples

The `lmod-ingest` utility is designed to provide a minimal command line interface.
Common use cases and examples are provided in the sections below.

## Database Migration

The `migrate` command will automatically apply the database schema required by the application.
This command should be run any time the utility is installed or updated/downgraded between versions
The application will automatically identify and apply the appropriate schema version.

```bash
lmod-ingest migrate
```

The `--sql` option enables a dry-run mode which prints the equivilent SQL commands without executing them.

```bash
lmod-ingest migrate --sql
```

## Data Ingestion

The `ingest` command is used to ingest data from a given log file.
Ingesting the same log file multiple times will not result in duplicate database entries.
The following example ingests the file `lmod.log`:

```bash
lmod-ingest ingest lmod.log
```

## Leveraging Database Views

The application database schema includes predefined views for user convenience.
