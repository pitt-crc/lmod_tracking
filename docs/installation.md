# Installation and Setup

Before installing the `lmod-ingest` utility, the following resources should already be configured in your environment:

- Lmod logging is configured and running on your cluster.
- Lmod system logs are proper configured for compatibility with the ingestion utility.
- A Postgres server is installed and configured with valid user credentials.

For more information on implementing accepted Lmod log formats, see the [log formatting guide](log_formatting.md).

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
For convenience, these values can also be defined in a `.ingest.env` file under the user's home directory.
Values defined in a `.ingest.env` file will always take precedence over existing environmental variables.

A list of application settings and their defaults is provided in the table below.

| Variable  | Default     | Description                               |
|-----------|-------------|-------------------------------------------|
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

# Setup and Execution

After configuring the database connection settings, the application database schema is applied using the `migrate` command.

```bash
lmod-ingest migrate
```

Use the `ingest` command to load a log file into the application database.
This command can be run multiple times on the same log file without ingesting duplicate database data.

```bash
lmod-ingest ingest lmod.log
```
