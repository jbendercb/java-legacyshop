.PHONY: migrate seed run test

migrate:
\talembic -c alembic.ini upgrade head

seed:
\tpython -m app.db.seed

run:
\tuvicorn app.main:app --reload

test:
\tpytest -q
