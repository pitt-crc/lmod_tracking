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
3. Migrate your database to the necessary schema
4. Run the data ingestion

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

## Ingesting Data

Use the `ingest.py` script to ingest data into the database by specifying one or more log files to ingest:

```bash
python ingest.py lmod.log 
```

The ingestion script can safely be run multiple times on the same log file without ingesting duplicate data.

It is recommended to set up daily log file rotations and use cron to ingest the most recent log file.
The following example assumes you are logging to `lmod.log` and rotating files using the naming
scheme `lmod.log-YYYYMMDD`.

```bash
python ingest.py $(ls -1v lmod.log-* | head -n 1)
```

