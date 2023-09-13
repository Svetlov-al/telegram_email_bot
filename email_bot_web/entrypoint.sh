#!/bin/bash

python3 manage.py migrate
python3 manage.py collectstatic --noinput

uvicorn email_bot_web.asgi:application --host 0.0.0.0 --port $WEB_PORT
