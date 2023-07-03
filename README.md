# LMOD Usage Tracking
[![](https://app.codacy.com/project/badge/Grade/da5fd23a62874c989f9b80ba201af924)](https://app.codacy.com/gh/pitt-crc/lmod_tracking/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

Lmod provides [official support](https://lmod.readthedocs.io/en/latest/300_tracking_load.html) for tracking module usage via the system log.
This repository provides scripts and utilities for ingesting the resulting log data into a MySQL database.

## Setup Instructions

It is assumed you already have a running MySQL server and Lmod logging is configured on your cluster.

If you don't want to read the full instructions (even though you really should), here is a high level summary:
1. Make sure your system logs are formatted properly
2. Create a new database and use the `create_tables.sql` script to establish the database schema
3. Create new database credentials and stash them in a `db.cnf` file
4. Run the `update_db.sh` as often as is necessary to ingest new log records into the database

### Configuring Lmod Logging

Lmod facilitates usage tracking by logging module loads to the system log.
This project assumes Lmod log messages are written using the following format:

```
[MONTH] [DAY] [TIME] [NODE] [LOGGERNAME]: user=[USERNAME] module=[PACKAGE]/[VERSION] path=[MODULEPATH] host=[NODE] time=[UTC]
```

For reference, here is a fully rendered example:

```
Apr 27 03:22:57 node1 ModuleUsageTracking: user=usr123 module=gcc/5.4.0 path=/modules/gcc/5.4.0.lua host=node1.domain.com time=1682580177.622180
```

At the time of writing, this is the same format suggested by the [official Lmod documentation](https://lmod.readthedocs.io/en/latest/300_tracking_load.html).
If your format differs from the above, it can be changed via the `SitePackage.lua` file.

### Configuring the Database

The `create_tables.sql` file will automatically create any database tables required by this project.
The following example demonstrates the initialization of a new database called `lmod`:

```mysql
CREATE DATABASE lmod;
USE lmod;
SOURCE create_tables.sql;
```

### Database Connection Settings

Database connection settings should be configured as environmental variables.
For convenience, these values can be defined in a `.env` file.
Setting values and their defaults are provided in the table below.

| Variable      | Default     | Description                             |
|---------------|-------------|-----------------------------------------|
| `DB_USER`     |             | Username for logging into the database. |
| `DB_PASSWORD` |             | Password for logging into the database. |
| `DB_HOST`     | `localhost` | Host running the MySQL database.        |
| `DB_PORT`     | `3306`      | Port for accessing the MySQL database.  |
| `DB_NAME`     | `lmod`      | Name of the database to write to.       |

The following example demonstrates a minimally valid `.env` file:

```bash
DB_USER=lmod_ingest
DB_PASSWORD=password123
```

## Ingesting Data

Use the `ingest.py` script to ingest data into the database by specifying one or more log files to ingest:

```bash
python ingest.py lmod.log 
```

It is recommended to set up daily log file rotations and use a cron job to ingest the most recent log file.
The following example assumes you are logging to `lmod.log` and rotating files using the naming scheme `lmod.log-YYYYMMDD`.

```bash
python ingest.py $(ls -1v lmod.log-* | head -n 1)
```

The ingestion script can safely be run multiple times on the same log file without ingesting duplicate data.

## Configuring Custom Views

Defining custom views is recommended for improving data abstraction and simplifying complex queries.
Views are **not** generated automatically when running an alembic migration and must be created manually.
However, a few useful examples are provided below.

### General Usage Overview

```mysql
CREATE VIEW module_usage AS
    SELECT
        user.name as user,
        package.name as package,
        package.version,
        module_load.load_time
    FROM
        module_load
    JOIN user ON user.id = module_load.user_id
    JOIN package ON package.id = module_load.package_id;
```

### Usage Counts by Package

The `package_count` view provides the name (`package`), total number of lmod loads (`count`), and last load
time (`last_load`) for each package.

```mysql
CREATE VIEW package_count AS
    SELECT 
        package.name AS package,
        COUNT(*)     AS count,
        max_date  AS last_load
    FROM 
        module_load
    JOIN package ON package.id = module_load.package_id
    JOIN (SELECT MAX(load_time) AS max_date FROM module_load) AS mu
    GROUP BY 
        package.name
    ORDER BY package;
```

### Usage Counts by Package and Version

The `package_version_count` view is similar to the `package_count` view except it provides an additional column for
package version (`version`).

```mysql
CREATE VIEW package_version_count AS
    SELECT package.name    AS package,
        package.version AS version,
        COUNT(*)        AS count,
        max_date     AS last_load
    FROM 
        module_load
    JOIN package ON package.id = module_load.package_id
    JOIN (SELECT MAX(load_time) AS max_date FROM module_load) AS mu
    GROUP BY 
        package.name, 
        package.version
    ORDER BY package;
```
