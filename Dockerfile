FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app/cafe_manager
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN pip install poetry
COPY . /app
RUN poetry config virtualenvs.create false && poetry install --no-root
EXPOSE 8000
RUN ls
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]