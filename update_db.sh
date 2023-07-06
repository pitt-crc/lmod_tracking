#!/usr/bin/env bash

# Determine the most recently rotated log file by its name
recent_file=$(ls -r lmod.log-* | head -n 1)

# Replace `lmod.log` with the new file path and execute the resulting sql
sed "s|lmod.log|$recent_file|g" ingest_data.sql | mysql --defaults-file=db.cnf -vvv
