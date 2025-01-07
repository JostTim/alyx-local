# syntax=docker/dockerfile:1

FROM rabbitmq:4-management

RUN apt-get update && \
    apt-get install -y dos2unix 

# COPY ./config/rabbitmq-password /run/secrets/rabbitmq-password
# COPY ./config/rabbitmq-user /run/secrets/rabbitmq-user

COPY ./docker/rabbitmq/entrypoint.sh /app/entrypoint.sh

RUN dos2unix -o /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]