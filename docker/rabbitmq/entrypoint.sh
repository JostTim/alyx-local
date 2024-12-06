#!/bin/bash
set -e

# Read the password from the file
if [ -f /run/secrets/rabbitmq-password ]; then
  export RABBITMQ_PASSWORD=$(cat /run/secrets/rabbitmq-password)
  export RABBITMQ_USER=$(cat /run/secrets/rabbitmq-user)
fi

# Execute the original entrypoint with the provided arguments
exec /usr/local/bin/docker-entrypoint.sh "$@"
