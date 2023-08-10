# LMOD Usage Tracking

[![](https://app.codacy.com/project/badge/Grade/da5fd23a62874c989f9b80ba201af924)](https://app.codacy.com/gh/pitt-crc/lmod_tracking/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

Lmod provides [official support](https://lmod.readthedocs.io/en/latest/300_tracking_load.html) for tracking
module usage via the system log.
This repository provides scripts and utilities for ingesting the resulting log data into a MySQL database.

## Setup Instructions

These instructions assume the following conditions are already met:

- Lmod logging is configured and running on your cluster.
- A MySQL server is installed and configured with valid user credentials.

In the sections below you will:

1. Ensure your log entries are properly formatted
2. Configure your database connection settings
3. Install and run the `lmod-ingest` commandline utility

### Lmod Log Formatting

This project assumes Lmod log messages are written to disk using the following format:

```
[MONTH] [DAY] [TIME] [NODE] [LOGGERNAME]: user=[USERNAME] module=[PACKAGE]/[VERSION] path=[MODULEPATH] host=[NODE] time=[UTC]
```

For reference, here is a fully rendered example:

```
Apr 27 03:22:57 node1 ModuleUsageTracking: user=usr123 module=gcc/5.4.0 path=/modules/gcc/5.4.0.lua host=node1.domain.com time=1682580177.622180
```

At the time of writing, this is the same format suggested by
the [official Lmod documentation](https://lmod.readthedocs.io/en/latest/300_tracking_load.html).
If your format differs from the above, you must change it by editing the `SitePackage.lua` file.

### Database Connection Settings

Database connection settings are configured as environmental variables.
For convenience, these values can be defined in a `.env` file.
A list of accepted variables and their defaults are provided in the table below.

| Variable  | Default     | Description                              |
| --------- | ----------- | ---------------------------------------- |
| `DB_USER` |             | User name for logging into the database. |
| `DB_PASS` |             | Password for logging into the database.  |
| `DB_HOST` | `localhost` | Host running the MySQL database.         |
| `DB_PORT` | `3306`      | Port for accessing the MySQL database.   |
| `DB_NAME` |             | Name of the database to write to.        |

The following example demonstrates a minimally valid `.env` file:

```bash
DB_USER=lmod_ingest
DB_PASS=password123
DB_NAME=lmod_tracking
```

## Application Setup and Execution

The `lmod-ingest` utility is pip installable:

```bash
pip install crc-lmod-ingest
lmod-ingest --help
```

Once installed, the necessary database schema can be applied using the `migrate` command.
Before running the command, make sure you have already created a `.env` file as described in the previous step.
The `--sql` option can be used to perform an initial dry run and priunt the migration SQL lgic without modifying the
database.

```bash
# Print the migratin SQL cmmands
lmod-ingest migrate --sql

# Execute the migration
lmod-ingest migrate
```

Use the `ingest` command to load ny desired log files into the application database.
The ingestion script can safely be run multiple times on the same log file without ingesting duplicate data.

```bash
lmod-ingest ingest lmog.log
```

The following example assumes you are logging to `lmod.log` and rotating files using the naming
scheme `lmod.log-YYYYMMDD`.

```bash
python ingest.py $(ls -1v lmod.log-* | head -n 1)
```

