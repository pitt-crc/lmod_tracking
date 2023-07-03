/* This script creates various views as a convenience to database users */

-- General overview summarizing all package loads.
CREATE VIEW module_usage AS
    SELECT
        user.name as user,
        package.name as package,
        package.version,
        module_load.load_time
    FROM module_load
    JOIN user ON user.id = module_load.user_id
    JOIN package ON package.id = module_load.package_id;

-- The name, total number of lmod loads, and last load time for each package.
CREATE VIEW package_version_count AS
    SELECT package.name    AS package,
        package.version AS version,
        COUNT(*)        AS count,
        max_date     AS last_load
    FROM module_load
    JOIN package ON package.id = module_load.package_id
    JOIN (SELECT MAX(load_time) AS max_date FROM module_load) AS mu
    GROUP BY
        package.name,
        package.version
    ORDER BY package;

-- The name, total number of lmod loads, and last load time for each package version.
CREATE VIEW package_count AS
SELECT
    package.name AS package,
    COUNT(*)     AS count,
    max_date  AS last_load
FROM module_load
         JOIN package ON package.id = module_load.package_id
         JOIN (SELECT MAX(load_time) AS max_date FROM module_load) AS mu
GROUP BY
    package.name
ORDER BY package;
