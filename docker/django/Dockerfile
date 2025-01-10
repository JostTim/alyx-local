# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12.3
ARG DEGUG=0
FROM python:${PYTHON_VERSION}-slim AS base

ARG APP_USER=appuser
ARG UID=10001

RUN echo "Building the Docker image..."

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=${DEBUG}

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

#########################################
# Create a non-root user to run the app #
RUN adduser \
    --disabled-password \
    --gecos "" \
    --shell "/sbin/nologin" \
    --home "/${APP_USER}" \
    --uid "${UID}" \
    ${APP_USER}


# get pg_restore and other database tools #
RUN apt-get update && \
    apt-get install -y wget gnupg2 lsb-release && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

RUN apt-get update && \
    apt-get install -y \
    postgresql-client-17 \
    dos2unix \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

########################################################
# Install PDM that will manage the python dependancies #
RUN pip install pdm

#################################################################
## Copy the django application source code into the container. ##
RUN mkdir -p /app/uploaded/static && \
    mkdir -p /app/uploaded/media

COPY ./pyproject.toml /app/pyproject.toml
COPY ./pdm.lock /app/pdm.lock

################################################
## ENSURE WE ACCESS THE ENTRYPOINT CORRECTLY  ##
COPY ./docker/django/entrypoint.sh /app/entrypoint.sh

#############################################################################
## ENSURE WE COPY CONFIG FILES GENERATED WITH INSTALL, IN PROPER LOCATIONS ##
COPY ./config/custom_settings.py /app/extra_configuration/custom_settings.py

##################################################################
## SET USER PERMISSIONS ON THE APP FOLDER AND ENTRYPOINT SCRIPT ##
RUN chown -R ${APP_USER}:${APP_USER} /app/

RUN dos2unix -o /app/entrypoint.sh
RUN chown ${APP_USER}:${APP_USER} /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

#############################################################
# Switch to the non-privileged user to run the application. #
USER ${APP_USER}

WORKDIR /app

# Expose the port that the application listens on.
EXPOSE 80

RUN echo "Launching the entrypoint script..."
CMD ["./entrypoint.sh"]