# LMOD Usage Tracking

Lmod provides [official support](https://lmod.readthedocs.io/en/latest/300_tracking_module_usage.html) for tracking
module usage via the system log.
This repository provides scripts and utilities for ingesting the resulting log data into a MySQL database.

## Setup Instructions

The following instructions assume the following conditions are already met:

- Lmod logging is already configured and running on your cluster.
- A MySQL server is already installed and configured with valid user credentials.
- The necessary Python requirements have been installed in your working environment (`pip install -r requirements.txt`).

### Lmod Logging

Lmod facilitates usage tracking by logging module loads to the system log.
This project assumes Lmod log messages are written using the following format:

```
[MONTH] [DAY] [TIME] [NODE] [LOGGERNAME]: user=[USERNAME] module=[PACKAGE]/[VERSION] path=[MODULEPATH] host=[NODE] time=[UTC]
```

For reference, here is a fully rendered example:

```
Apr 27 03:22:57 node1 ModuleUsageTracking: user=usr123 module=gcc/5.4.0 path=/modules/gcc/5.4.0.lua host=node1.domain.com time=1682580177.622180
```

At the time of writing, this is the same format suggested by
the [official Lmod documentation](https://lmod.readthedocs.io/en/latest/300_tracking_module_usage.html).
If your format differs from the above, it can be changed via the `SitePackage.lua` file.

### Database Connecting Settings

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

### Database Schema

Migration recipes are provided for automatically configuring the necessary database schema.
Start by creating a new database.
Make sure the database name is the same as the name configured in the application connection settings.

```bash
mysql -u <username> -p -e "CREATE DATABASE lmod;"
```

Next, use alembic to apply the necessary schema:

```bash
alembic upgrade 0.1  # 0.1 is the latest DB schema version
```

## Ingesting Data

Use the `ingest.py` script to ingest data into the database by specifying one or more log files to ingest:

```bash
python ingest.py lmod.log 
```

It is recommended to set up daily log file rotations and use a chron jon to ingest the most recent log file.
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
CREATE VIEW overview AS
SELECT user.name    as user,
       package.name as package,
       package.version,
       module_usage.load_time
FROM module_usage
         JOIN user ON user.id = module_usage.user_id
         JOIN package ON package.id = module_usage.package_id;
```

### Usage Counts by Package

The `package_count` view provides the name (`package`, total number of lmod loads (`count`), and last load
time (`last_load`) for each package.

```mysql
CREATE VIEW package_count AS
SELECT package.name AS package,
       COUNT(*)     AS count,
       mu.max_date  AS last_load
FROM module_usage
         JOIN
     package ON package.id = module_usage.package_id
         JOIN
         (SELECT MAX(load_time) AS max_date FROM module_usage) AS mu
GROUP BY package.name, mu.max_date
ORDER BY count DESC;
```

### Usage Counts by Package and Version

The `package_version_count` view is similar to the `package_count` view except it provides an additional column for
package version (`version`).

```mysql
CREATE VIEW package_version_count AS
SELECT package.name    AS package,
       package.version AS version,
       COUNT(*)        AS count,
       mu.max_date     AS last_load
FROM module_usage
         JOIN
     package ON package.id = module_usage.package_id
         JOIN
         (SELECT MAX(load_time) AS max_date FROM module_usage) AS mu
GROUP BY package.name, package.version, mu.max_date
ORDER BY count DESC;
```