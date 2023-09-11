FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY ./pyproject.toml .
COPY ./poetry.lock .

RUN pip install poetry

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY ./email_bot_web .

CMD ["gunicorn", "--bind", "0:8000", "email_bot_web.wsgi:application"]
