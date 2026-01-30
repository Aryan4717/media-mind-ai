#!/bin/bash
set -e

# Copy custom pg_hba.conf to PostgreSQL data directory
# This runs after initdb completes but before the server starts accepting connections
if [ -f /docker-entrypoint-initdb.d/pg_hba.conf ]; then
    echo "Configuring pg_hba.conf for Docker network access..."
    cp /docker-entrypoint-initdb.d/pg_hba.conf "$PGDATA/pg_hba.conf"
    echo "PostgreSQL pg_hba.conf configured successfully"
fi

