FROM postgres:latest

# Copy the password file if it exists, otherwise use a default password
COPY ./config/db-default-password /run/secrets/db-secure-password
ENV POSTGRES_PASSWORD_FILE=/run/secrets/db-secure-password