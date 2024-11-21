# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12.3

FROM python:${PYTHON_VERSION}-slim AS base

ARG APP_USER=appuser
ARG UID=10001

RUN echo "Building the Docker image..."

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

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
    apt-get install -y \
    postgresql-client \
    dos2unix \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

########################################################
# Install PDM that will manage the python dependancies #
RUN pip install pdm

#########################################################################
# CREATE VOLUMES FOLDER IF EMPTY AND SET PERMISSIONS ON THE APP FOLDER ##
# RUN mkdir -p /app/alyx/ && \
#     mkdir -p /app/uploaded/log && \
#     mkdir -p /app/uploaded/static && \
#     mkdir -p /app/uploaded/media && \
#     mkdir -p /app/uploaded/tables && \
#     chown -R ${APP_USER}:${APP_USER} /app/

#################################################################
## Copy the django application source code into the container. ##
COPY ./src/ /app/
COPY ./pyproject.toml /app/pyproject.toml
COPY ./pdm.lock /app/pdm.lock
COPY ./docker/install_config /app/alyx/config/

########################################################################
## ENSURE WE COPY ALL SHELL SCRIPTS INTO THE APP FOLDER FOR LATER USE ##
COPY ./scripts/ /app/alyx/scripts

#####################################################
## ENSURE WE COPY ALL DUMPS DATA IF THERE ARE SOME ##
COPY ./data/ /data

################################################
## ENSURE WE ACCESS THE ENTRYPOINT CORRECTLY  ##
COPY ./docker/django/entrypoint.sh /app/entrypoint.sh
COPY ./docker/django/restore_on_run.sh /app/alyx/scripts/restore_on_run.sh

RUN dos2unix -o /app/entrypoint.sh
RUN chown ${APP_USER}:${APP_USER} /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# we run chmod executeable, chown user, and we ensure scripts are LF ended with dos2unix
RUN find /app/alyx/scripts -type f -name "*.sh" \
    -exec dos2unix -o {} \; \ 
    -exec chmod +x {} \; \
    && \
    chown -R ${APP_USER}:${APP_USER} /app/alyx/scripts

#############################################################
# Switch to the non-privileged user to run the application. #
USER ${APP_USER}

WORKDIR /app

# Install the application python dependancies packages
RUN pdm install --prod --frozen-lockfile --no-editable

# Expose the port that the application listens on.
EXPOSE 80

RUN echo "Launching the entrypoint script..."
CMD ["./entrypoint.sh"]