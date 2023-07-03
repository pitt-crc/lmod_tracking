# LMOD Usage Tracking
[![](https://app.codacy.com/project/badge/Grade/da5fd23a62874c989f9b80ba201af924)](https://app.codacy.com/gh/pitt-crc/lmod_tracking/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

Lmod provides [official support](https://lmod.readthedocs.io/en/latest/300_tracking_module_usage.html) for tracking module usage via the system log.

This repository provides scripts and utilities for ingesting the resulting log data into a MySQL database.

## Setup Instructions

The following instructions walk through the initialization of a new MySQL database and any related configuration details.
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

At the time of writing, this is the same format suggested by the official [Lmod documentation](https://lmod.readthedocs.io/en/latest/300_tracking_module_usage.html).
If your format differs from the above, it can be changed via the `SitePackage.lua` file (see the Lmod documentation for specifics).

### Configuring the Database

The `create_tables.sql` file will automatically create any database tables required by this project.
The following example demonstrates the initialization of a new database called `lmod`:


```mariadb
CREATE DATABASE lmod;
USE lmod;
SOURCE create_tables.sql;
```

The `create_views` defines views for improving data abstraction and simplifying complex queries.
These views are not required, but are recommended as a useful starting point.
Ultimately, you will want to implement custom views designed specifically for your team's use case.

```mariadb
SOURCE create_tables.sql;
```

When operating in production, it is recommended to use a service account to facilitate data ingestion tasks.
The following snippet creates a service account `lmod_service` with access to the `lmod` database.
Make sure to replace the password `password123` with a secure alternative.

```mariadb
CREATE USER 'lmod_service'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON lmod.* TO 'lmod_service'@'localhost';
FLUSH PRIVILEGES;
```

### Database Connection Settings

Todo: document the db.cnf file.

## Ingesting Data

Todo: document the shell script
    JOIN package ON package.id = module_load.package_id
    JOIN (SELECT MAX(load_time) AS max_date FROM module_load) AS mu
    GROUP BY 
        package.name, 
        package.version
    ORDER BY package;
```
