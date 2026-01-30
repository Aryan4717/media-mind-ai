#!/bin/bash
set -e

# Call the original PostgreSQL entrypoint
exec /usr/local/bin/docker-entrypoint.sh "$@"

