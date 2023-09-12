SHELL := /bin/bash

up:
	docker compose up

up-d:
	docker compose up -d

down:
	docker compose down

up-b:
	docker compose up --build

up-bd:
	docker compose up --build -d

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

collectstatic:
	docker compose exec web python manage.py collectstatic

createsuperuser:
	docker compose exec web python manage.py createsuperuser