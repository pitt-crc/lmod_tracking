# Lmod Usage Tracking

[![](https://app.codacy.com/project/badge/Grade/da5fd23a62874c989f9b80ba201af924)](https://app.codacy.com/gh/pitt-crc/lmod_tracking/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![](https://app.codacy.com/project/badge/Coverage/da5fd23a62874c989f9b80ba201af924)](https://app.codacy.com/gh/pitt-crc/lmod_tracking/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage)

Lmod provides [official support](https://lmod.readthedocs.io/en/latest/300_tracking_module_usage.html) for tracking module usage via the system log.
This repository provides scripts and utilities for ingesting the resulting log data into a Postgres database.

## Setup Instructions

These instructions assume the following conditions are already met:

- Lmod logging is configured and running on your cluster.
- A Postgres server is installed and configured with valid user credentials.

In the sections below you will:

1. Ensure your log entries are properly formatted.
2. Configure your database connection settings.
3. Install and run the `lmod-ingest` command-line utility.

### Lmod Log Formatting

This project assumes Lmod log messages are written to disk using the following format:

```
[MONTH] [DAY] [TIME] [NODE] [LOGGERNAME]: user=[USERNAME] module=[PACKAGE]/[VERSION] path=[MODULEPATH] host=[NODE] time=[UTC]
```

For reference, here is a fully rendered example:

```
Apr 27 03:22:57 node1 ModuleUsageTracking: user=usr123 module=gcc/5.4.0 path=/modules/gcc/5.4.0.lua host=node1.domain.com time=1682580177.622180
```

At the time of writing, this is the same format suggested by the official Lmod documentation.
If your format differs from the above, you must change it by editing the `SitePackage.lua` file.

### Database Connection Settings

Database connection settings are configured as environmental variables.
For convenience, these values can be defined in a `.ingest.env` file under the user's home directory.
A list of accepted variables and their defaults is provided in the table below.

| Variable  | Default     | Description                               |
|-----------|-------------|-------------------------------------------|
| `DB_USER` |             | User name for logging into the database.  |
| `DB_PASS` |             | Password for logging into the database.   |
| `DB_HOST` | `localhost` | Host running the Postgres database.       |
| `DB_PORT` | `3306`      | Port for accessing the Postgres database. |
| `DB_NAME` |             | Name of the database to write to.         |

The following example demonstrates a minimally valid `.ingest.env` file:

```bash
DB_USER=lmod_ingest
DB_PASS=password123
DB_NAME=lmod_tracking
```

## Application Setup and Execution

The `lmod-ingest` utility is pip installable.
If you have access to the CRC package repository, the package can be using the commands below.
Alternatively, the package can be installed directly from the GitHub repository.

```bash
pipx install lmod-ingest
lmod-ingest --help
```

Once installed, the necessary database schema can be applied using the `migrate` command.
Before running the command, make sure you have already created a `.ingest.env` file as described in the previous step.
The `--sql` option can be used to perform an initial dry run and print the migration SQL logic without modifying the database.

```bash
# Print the migration SQL commands
lmod-ingest migrate --sql

# Execute the migration
lmod-ingest migrate
```

Use the `ingest` command to load a log file into the application database.
The ingestion script can safely be run multiple times on the same log file without ingesting duplicate data.

```bash
lmod-ingest ingest lmod.log
```
