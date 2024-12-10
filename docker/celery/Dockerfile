FROM python:3.12-slim AS base

RUN pip install flower pyamqp

CMD ["sh",  "-c",  "celery --broker=pyamqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672// flower --port=5001 --address=0.0.0.0 --basic_auth=${FLOWER_USER}:${FLOWER_PASSWORD}"]