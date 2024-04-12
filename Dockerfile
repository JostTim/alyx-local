# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.12.3
FROM python:${PYTHON_VERSION}-slim as base

ARG APP_USER=appuser
ARG UID=10001

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1


# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/

RUN adduser \
    --disabled-password \
    --gecos "" \
    --shell "/sbin/nologin" \
    --home "/${APP_USER}" \
    --uid "${UID}" \
    ${APP_USER}


WORKDIR /app

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.

# Copy the source code into the container.

RUN mkdir -p /app/alyx/ && \
    chown ${APP_USER}:${APP_USER} /app/alyx/

RUN mkdir -p /app/uploaded/log && \
    chown ${APP_USER}:${APP_USER} /app/uploaded/log/

RUN mkdir -p /app/uploaded/static && \
    chown ${APP_USER}:${APP_USER} /app/uploaded/static/

RUN mkdir -p /app/uploaded/media && \
    chown ${APP_USER}:${APP_USER} /app/uploaded/media/

RUN mkdir -p /app/uploaded/tables && \
chown ${APP_USER}:${APP_USER} /app/uploaded/tables/

COPY ./alyx/ /app/alyx/
COPY ./.production/entrypoint.sh /app/alyx/entrypoint.sh

RUN chown ${APP_USER}:${APP_USER} /app/alyx/entrypoint.sh
RUN chmod +x /app/alyx/entrypoint.sh

USER ${APP_USER}

WORKDIR /app/alyx

# Expose the port that the application listens on.
EXPOSE 80

# Start Nginx and Gunicorn
# Run the application.
CMD ["/app/alyx/entrypoint.sh"]
#CMD gunicorn 'alyx.wsgi' --bind=0.0.0.0:8000
