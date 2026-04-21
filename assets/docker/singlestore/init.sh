#!/bin/bash
set -e

# Start SingleStore in the background
/scripts/start.sh &

# Wait for SingleStore to accept connections
until singlestore -p"${ROOT_PASSWORD:-test_superuser}" -e "SELECT 1;" 2>/dev/null; do
    sleep 2
done

# Create the test database
singlestore -p"${ROOT_PASSWORD:-test_superuser}" -e "CREATE DATABASE IF NOT EXISTS test_ci;"

# Wait for the background process
wait
