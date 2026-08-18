# Lmod Usage Tracking

A simple command line tool for ingesting Lmod log data into a PostgreSQL database.

[Lmod](https://lmod.readthedocs.io/en/latest/index.html) is a popular utility for managing user runtime environments on
supercomputing clusters. To better understand system usage patterns, many system administrators leverage Lmod logs to
track what software is being loaded by users and where. The lmod-ingest utility is a simple ETL tool used to ingest Lmod
log records into a Postgres database in a useful format.

## Prerequisites

Before installing the `lmod-ingest` utility, the following resources should already be configured in your environment:

- Lmod logging is configured and running on your cluster.
- Lmod system logs are formatted for compatibility with the ingestion utility (see below).
- A Postgres server is installed and configured with valid user credentials.

### LMOD Log Formatting

This project assumes Lmod log messages are written to disk using the following format.
Log entries **must** follow this format to be parsable by the `lmod-ingest` application.

```text
[SYSLOG PREFIX] user=[USERNAME] jobid=[JOBID] module=[PACKAGE]/[VERSION] path=[MODULEPATH] host=[HOSTNAME] time=[UTC]
```

Individual field values are defined as follows:

| Field           | Description                                                              |
|-----------------|----------------------------------------------------------------------------|
| `SYSLOG PREFIX` | A system specific message prefix added by syslog. This value is ignored. |
| `USERNAME`      | The name of the user who loaded the module.                              |
| `JOBID`         | The nullable (`nil`) ID of the slurm job the module was loaded from.      |
| `PACKAGE`       | The name of the package loaded via lmod.                                 |
| `VERSION`       | The version of the pacakge loaded via lmod.                              |
| `MODULEPATH`    | The path of the loaded module file.                                      |
| `HOSTNAME`      | The machine hostname where the module was loaded.                        |
| `UTC`           | The UTC time the module was loaded.                                      |

If your cluster's format differs from the above, you must change it by editing the `SitePackage.lua` file.
The specific location of this file will vary depending on your Slurm cluster setup.

Appending the following code to the bottom of your `SitePackage.lua` file will send lmod messages to syslog using the required format.
Note the slurm Job ID is determined using the nullable environmental variable `SLURM_JOB_ID`
(and not the older, deprecated variable `SLURM_JOBID`).

```lua
--------------------------------------------------------------------------

require("lmod_system_execute")
local hook    = require("Hook")
local uname   = require("posix").uname
local s_msgA = {}

function load_hook(t)
   -- the arg t is a table:
   --     t.modFullName:  the module full name: (i.e: gcc/4.7.2)
   --     t.fn:           The file name: (i.e /apps/modulefiles/Core/gcc/4.7.2.lua)

   if (mode() ~= "load") then return end
   local user        = os.getenv("USER")
   local jobid       = os.getenv("SLURM_JOB_ID") or "nil"
   local host        = uname("%n")
   local currentTime = epoch()
   local msg         = string.format("'user=%s jobid=%s module=%s path=%s host=%s time=%f'",
                                     user, jobid, t.modFullName, t.fn, host, currentTime)
   local a           = s_msgA
   a[#a+1]           = msg
end

-- By using the hook.register function, the function "load_hook" is called
-- ever time a module is loaded with the file name and the module name.
hook.register("load",load_hook)

function report_loads()

   local sys         = os.getenv("LMOD_sys") or "Linux"
   if (sys == "Linux") then
      local a = s_msgA
      for i = 1,#a do
         local msg = a[i]
         lmod_system_execute("logger -t ModuleUsageTracking -p local0.info " .. msg)
      end
   end

end

ExitHookA.register(report_loads)
```

## Installation

### 1. Install the Package

The `lmod-ingest` utility is pip installable:

```bash
pipx install lmod-ingest
```

You can verify the installation is successful using the following command:

```bash
lmod-ingest --version
```

### 2. Configure Database Settings

Database connection settings are configured using environmental variables.
For convenience, these values can also be defined in a `.ingest.env` file under the user's home directory.
Values defined in a `.ingest.env` file will always take precedence over existing environmental variables.

A list of application settings and their defaults is provided in the table below.

| Variable  | Default     | Description                               |
|-----------|-------------|--------------------------------------------|
| `DB_USER` |             | User name for logging into the database.  |
| `DB_PASS` |             | Password for logging into the database.   |
| `DB_HOST` | `localhost` | Host running the Postgres database.       |
| `DB_PORT` | `3306`      | Port for accessing the Postgres database. |
| `DB_NAME` |             | Name of the database to write to.         |

The following example demonstrates a minimally valid `.ingest.env` file.
Administrators are reminded to **always** choose a secure database password when operating in a production environment.

```bash
DB_USER=lmod_ingest
DB_PASS=password123
DB_NAME=lmod_tracking
```

### 3. Apply the Database Schema

Once the database settings are configured, apply the database schema using the `migrate` command.
This command automatically identifies and applies the appropriate schema version, and should be re-run any time the utility is updated or downgraded to a new version.

```bash
lmod-ingest migrate
```

The `--sql` option enables a dry-run mode which prints the equivalent SQL commands without executing them.

```bash
lmod-ingest migrate --sql
```

With the schema in place, `lmod-ingest` is ready to start ingesting log data.

## Usage

Once setup is complete, use the following commands and queries for day-to-day operation.

### Data Ingestion

The `ingest` command is used to ingest data from a given log file.
Ingesting the same log file multiple times will not result in duplicate database entries.
The following example ingests the file `lmod.log`:

```bash
lmod-ingest ingest lmod.log
```

### Leveraging Database Views

The application database schema includes predefined views for user convenience.
Available database tables and views are listed in the table below.

| View                     | View/Table | Description                                                          |
|--------------------------|------------|------------------------------------------------------------------------|
| `log_data`               | Table      | The raw ingested Lmod log data.                                      |
| `unique_loads`           | View       | The same as `log_data` but each entry represents a unique slurm job. |
| `package_count`          | View       | The total number of times a package has been used in a slurm job.    |
| `package_version_count`  | View       | The same as `package_count` but broken down by version.              |

#### Query Examples

All packages loaded from within a Slurm job between Jan 1 2023 and Jan 1 2024

```sql
SELECT DISTINCT package
FROM unique_loads
WHERE time >= '2023-01-01' AND time < '2024-01-01';
```

The number of times a specific package has been loaded outside a slurm job

```sql
SELECT package, COUNT(*) AS load_count
FROM log_data
WHERE jobid IS NULL
GROUP BY package;
```

The total number of unique users who have loaded each package in the past month ordered by decreasing popularity

```sql
SELECT
    package,
    COUNT(DISTINCT "user") AS unique_user_count
FROM log_data
WHERE 
    jobid IS NULL AND
    time >= NOW() - INTERVAL '1 month' AND time < NOW()
GROUP BY package
ORDER BY unique_user_count DESC;
```
