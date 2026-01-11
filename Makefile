.PHONY: help migrate run test docker-up docker-down

help:
	@echo "Доступные команды:"
	@echo "  make migrate    - Выполнить миграции"
	@echo "  make run        - Запустить сервер разработки"
	@echo "  make test       - Запустить тесты"
	@echo "  make docker-up  - Запустить Docker Compose"
	@echo "  make docker-down - Остановить Docker Compose"

migrate:
	python manage.py makemigrations
	python manage.py migrate

run:
	python manage.py runserver

test:
	pytest

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

