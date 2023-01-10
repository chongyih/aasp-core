FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update
RUN apt-get install -y build-essential

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY buffalo_l.zip /root/.insightface/models/buffalo_l.zip
RUN unzip buffalo_l.zip