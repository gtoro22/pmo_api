.PHONY: help install test run docker-build docker-run clean

ARGS ?= --help

help:
	@echo "make install       Instala el paquete en modo editable"
	@echo "make test          Ejecuta las pruebas"
	@echo "make run ARGS=...  Ejecuta el invocador localmente"
	@echo "make docker-build  Construye la imagen Docker"
	@echo "make docker-run ARGS=...  Ejecuta el invocador en Docker"
	@echo "make clean         Elimina artefactos generados"

install:
	python -m pip install -r requirements-dev.txt
	python -m pip install -e .

test:
	python -m pytest -q

run:
	python -m tracking_goals $(ARGS)

docker-build:
	docker compose build

docker-run:
	docker compose run --rm tracking-goals $(ARGS)

clean:
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
