FROM python:3.11-slim

LABEL maintainer="danilsivkovic@gmail.com"
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libffi-dev \
    libpq-dev \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

RUN python -m playwright install --with-deps

COPY . .
