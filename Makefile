SHELL := /bin/bash

up:
	docker compose up

up-d:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

collectstatic:
	docker compose exec web python manage.py collectstatic

createsuperuser:
	docker compose exec web python manage.py createsuperuser
