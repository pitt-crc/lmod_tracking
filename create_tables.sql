/* This script establishes the DB schema and creates any necessary tables */

-- Stores unique user information
CREATE TABLE `user`
(
    `id`   INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    INDEX `name_index` (`name`)
);

-- Stores package names and metadata
CREATE TABLE `package`
(
    `id`      INT AUTO_INCREMENT PRIMARY KEY,
    `name`    VARCHAR(100) NOT NULL,
    `version` VARCHAR(100),
    `path`    VARCHAR(200) NOT NULL UNIQUE
);

-- Stores machine host names
CREATE TABLE `host`
(
    `id`   INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    INDEX `name_index` (`name`)
);

-- Stores records for each time a package is laded via lmod
CREATE TABLE `module_load`
(
    `id`         INT AUTO_INCREMENT PRIMARY KEY,
    `user_id`    INT         NOT NULL,
    `host_id`    INT         NOT NULL,
    `package_id` INT         NOT NULL,
    `load_time`  DATETIME(6) NOT NULL,
    CONSTRAINT `fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
    CONSTRAINT `fk_host_id` FOREIGN KEY (`host_id`) REFERENCES `host` (`id`),
    CONSTRAINT `fk_package_id` FOREIGN KEY (`package_id`) REFERENCES `package` (`id`),
    INDEX `idx_package_id` (`package_id`)
);
