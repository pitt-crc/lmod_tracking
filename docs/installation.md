# Installation and Setup

The `lmod-ingest` utility is installed in four steps:  

1. Ensure your system satisfies the preliminary system requirements.
2. Pip install the `lmod-ingest` utility.
3. Configure the database connection settings.
4. Migrate the database schema and run the `lmod-ingest` command-line utility.

## System Prerequisites

These instructions assume the following conditions are already met:

- Lmod logging is configured and running on your cluster.
- Lmod system logs are proper configured for compatibility with the ingestion utility.
- A Postgres server is installed and configured with valid user credentials.

For more information on implementing accepted log formats, see the [log formatting guide](log_formatting.md).

## Package Installation

The `lmod-ingest` utility is pip installable:

```bash
pipx install lmod-ingest
```

You can verify the installation is successful using the following command:

```bash
lmod-ingest --version
```

## Database Settings

Database connection settings are configured using environmental variables.
For convenience, these values can alternatively be defined in a `.ingest.env` file under the user's home directory.
Values defined in a `.ingest.env` file will always take precedence over existing environmental variables.

A list of accepted variables and their defaults is provided in the table below.

| Variable  | Default     | Description                               |
|-----------|-------------|-------------------------------------------|
| `DB_USER` |             | User name for logging into the database.  |
| `DB_PASS` |             | Password for logging into the database.   |
| `DB_HOST` | `localhost` | Host running the Postgres database.       |
| `DB_PORT` | `3306`      | Port for accessing the Postgres database. |
| `DB_NAME` |             | Name of the database to write to.         |

The following example demonstrates a minimally valid `.ingest.env` file.
**Always** choose a secure database password when operating in a production environment.

```bash
DB_USER=lmod_ingest
DB_PASS=password123
DB_NAME=lmod_tracking
```

# Setup and Execution

After configuring the database connection settings, the application database schema is applied using the `migrate` command.

```bash
lmod-ingest migrate
```

Use the `ingest` command to load a log file into the application database.
The ingestion script can safely be run multiple times on the same log file without ingesting duplicate data.

```bash
lmod-ingest ingest lmod.log
```
