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

### Load Counts by Package

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

### Load Counts by Package and Version

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