# makes `make test` target our test section, not the directory test/
.PHONY: test

curr_dir = $(shell pwd)

run:
	docker-compose up app webpack worker

run-detached:
	docker-compose up -d app webpack worker

run-scheduler:
	docker-compose up -d scheduler

stop:
	docker-compose stop

destroy:
	docker-compose down -v

test:
	tox -e tests

pytest:
	.tox/tests/bin/py.test

fake:
	docker-compose run app django-admin fake

migrate:
	docker-compose run app django-admin migrate

migrations:
	docker-compose run app django-admin makemigrations

superuser:
	docker-compose run app django-admin createsuperuser

bash:
	docker-compose run app bash

django-shell:
	docker-compose run -u macaque app django-admin shell

build-docs:
	(cd docs && make html)

open-docs:
	open docs/_build/html/index.html
