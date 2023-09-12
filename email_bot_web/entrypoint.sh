#!/bin/bash

python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic --noinput

python3 manage.py runserver 0.0.0.0:8000
#uvicorn email_bot_web.asgi:application --host 0.0.0.0 --port 8000