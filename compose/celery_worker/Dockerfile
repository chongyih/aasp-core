FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get install -y build-essential

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

WORKDIR /app

ENTRYPOINT celery -A aasp worker --loglevel=INFO
