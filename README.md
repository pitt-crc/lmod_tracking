# LMOD Usage Tracking

This repository provides scripts and utilities to help facilitate tracking of LMOD pacakge usage.

## Module Tracking Setup

## Database Ingestion

When setting up their database, users may also find it useful to define views summarizing the overall package usage.

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