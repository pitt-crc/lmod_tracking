# LMOD Usage Tracking

Lmod provides [official support](https://lmod.readthedocs.io/en/latest/300_tracking_module_usage.html) for tracking
module usage via the system log.
This repository provides scripts and utilities for ingesting the resulting log data into a MySQL database.

## Setup and Background

This project assumes Lmod usage data is written to disk using the following plain text data model:

```
[MONTH] [DAY] [TIME] [NODE] [LOGGERNAME]: user=[USERNAME] module=[PACKAGE]/[VERSION] path=[MODULEPATH] host=[NODE] time=[UTC]
```

## Database Ingestion

When setting up their database, users may also find it useful to define views summarizing the overall package usage.

## Configuring Custom Views

Defining custom views is recommended for improving data abstraction and simplifying complex queries.
Views are **not** generated automatically when running an alembic migration and must be created manually.
However, a few useful examples are provided below.

### General Usage Overview

```mysql
CREATE VIEW overview AS 
    SELECT 
        user.name as user, 
        package.name as package, 
        package.version,
        module_usage.load_time 
    FROM 
        module_usage 
    JOIN user ON user.id = module_usage.user_id 
    JOIN package ON package.id = module_usage.package_id;
```

### Usage Counts by Package

The `package_count` view provides the name (`package`, total number of lmod loads (`count`), and last load time (`last_load`) for each package.

```mysql
CREATE VIEW package_count AS
    SELECT
        package.name AS package,
        COUNT(*) AS count,
        mu.max_date AS last_load
    FROM
        module_usage
            JOIN
        package ON package.id = module_usage.package_id
            JOIN
            (SELECT MAX(load_time) AS max_date FROM module_usage) AS mu
    GROUP BY
        package.name, mu.max_date
    ORDER BY
        count DESC;
```

### Usage Counts by Package and Version

The `package_version_count` view is similar to the `package_count` view except it provides an additional clumn for package version (`version`).

```mysql
CREATE VIEW package_version_count AS
    SELECT
        package.name AS package,
        package.version AS version,
        COUNT(*) AS count,
        mu.max_date AS last_load
    FROM
        module_usage
            JOIN
        package ON package.id = module_usage.package_id
            JOIN
            (SELECT MAX(load_time) AS max_date FROM module_usage) AS mu
    GROUP BY
        package.name, package.version, mu.max_date
    ORDER BY
        count DESC;
```