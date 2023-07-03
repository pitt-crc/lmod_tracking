/* This script ingests data from a module log file into the database. */

-- Create a temporary table for storing unprocessed data loaded from
CREATE TEMPORARY TABLE scratch
(
    month   CHAR(3),
    day     INTEGER,
    time    DATETIME(6),
    node    VARCHAR(25),
    logname VARCHAR(100),
    user    VARCHAR(100),
    module  VARCHAR(100),
    path    VARCHAR(300)
);

-- Load data from disk into the scratch table
LOAD DATA LOCAL INFILE 'lmod.log' INTO TABLE scratch FIELDS TERMINATED BY ' ';

-- Clean the ingested data by dropping prefixes generated in the log file
UPDATE scratch SET user = REPLACE(user, "user=", "");
UPDATE scratch SET module = REPLACE(module, "module=", "");
UPDATE scratch SET path = REPLACE(path, "path=", "");

-- Update the `node` and `user` tables with any new entries. Ignore conflicts from duplicates.
INSERT IGNORE INTO host (name) SELECT node AS name FROM scratch;
INSERT IGNORE INTO user (name) SELECT user AS name FROM scratch;

/* Split package/version values into separate values for package and version
   Use regex to account for some version values including slashes */
INSERT IGNORE INTO package (name, version, path)
    SELECT
        substring_index(module, '/', 1) AS name,
        regexp_replace(module, '^[^\/]*\/?', '') AS version,
        path
    FROM scratch;

-- Perform joins to determine foreign key values and insert the results into the `module_load` table
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
