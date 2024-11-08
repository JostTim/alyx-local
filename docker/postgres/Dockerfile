FROM postgres:latest

# Copy the password file if it exists, otherwise use a default password
COPY ./docker/postgres/db-default-password ./docker/postgres/*password /run/secrets/
RUN if [ ! -f /run/secrets/db-secure-password ]; \
    then cp /run/secrets/db-default-password /run/secrets/db-secure-password; \
    fi

ENV POSTGRES_PASSWORD_FILE=/run/secrets/db-secure-password