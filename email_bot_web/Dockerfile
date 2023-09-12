FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY ./pyproject.toml .
COPY ./poetry.lock .

RUN pip install poetry==1.5.1

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY ./email_bot_web .

# CMD ["uvicorn", "email_bot_web.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]