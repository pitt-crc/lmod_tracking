# The scratch table is used to temporarily hold data loaded from disk while it is ingested into the DB schema
DROP TABLE IF EXISTS scratch;
CREATE TABLE scratch
(
    month   CHAR(3),
    day     INTEGER,
    time    CHAR(8),
    node    VARCHAR(25),
    logname VARCHAR(100),
    user    VARCHAR(100),
    module  VARCHAR(100),
    path    VARCHAR(300)
);

# Load data from disk into the scratch table
LOAD DATA LOCAL INFILE 'moduledb/lmod.log-20230427' INTO TABLE scratch FIELDS TERMINATED BY ' ';

# Drop prefixes generated in the log file
UPDATE scratch SET user = REPLACE(user, "user=", "");
UPDATE scratch SET module = REPLACE(module, "module=", "");
UPDATE scratch SET path = REPLACE(path, "path=", "");

# Update the `node` and `user` tables with any new entries
INSERT IGNORE INTO host (name) SELECT DISTINCT node AS name FROM scratch;
INSERT IGNORE INTO user (name) SELECT DISTINCT user AS name FROM scratch;

# Split package/version values into separate values for package and version
INSERT IGNORE INTO package (name, version, path)
SELECT DISTINCT
    substring_index(module, '/', 1) AS name,
    REGEXP_REPLACE(module, '^[^\/]*\/?', '') AS version,
    path
FROM scratch;

INSERT INTO module_load (user_id, host_id, package_id, load_time)
 SELECT
    user.id as user_id,
    host.id as host_id,
    package.id as package_id,
    scratch.time as load_time
FROM scratch
JOIN user ON user.name = scratch.user
JOIN host ON host.name = scratch.node
JOIN package ON package.name = substring_index(scratch.module, '/', 1);

COMMIT;
