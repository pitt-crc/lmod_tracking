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

The `--sql` option enables a dry-run mode which prints the equivalent SQL commands without executing them.

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
Available database tables and views are listed in the table below.

| View                    | View/Table | Description                     |
|-------------------------|------------|---------------------------------|
| `unique_loads`          | Table      | The raw ingested Lmod log data. |
| `unique_loads`          | View       |                                 |
| `package_count`         | View       |                                 |
| `package_version_count` | View       |                                 |

### Query Examples

All packages loaded from within a Slurm job between Jan 1 2023 and Jan 1 2024

```sql
SELECT DISTINCT package
FROM unique_loads
WHERE time >= '2023-01-01' AND time < '2024-01-01';
```

The number of times a specific package has been loaded outside a slurm job

```sql
SELECT package, COUNT(*) AS load_count
FROM log_data
WHERE jobid IS NULL
GROUP BY package;
```

The total number of unique users who have loaded each package in the past month ordered by decreasing popularity

```sql
SELECT
    package,
    COUNT(DISTINCT "user") AS unique_user_count
FROM log_data
WHERE 
    jobid IS NULL AND
    time >= NOW() - INTERVAL '1 month' AND time < NOW()
GROUP BY package
ORDER BY unique_user_count DESC;
```