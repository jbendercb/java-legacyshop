.PHONY: migrate seed run test

migrate:
	alembic -c alembic.ini upgrade head

seed:
	python -m app.db.seed

run:
	uvicorn app.main:app --reload

test:
	pytest -q
