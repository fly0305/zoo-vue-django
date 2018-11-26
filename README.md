# zoo

A smart service catalogue providing an overview of your services' development and
operations.

[![Python: 3.6](https://img.shields.io/badge/python-3.7-blue.svg)](https://python.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-black.svg)](https://github.com/ambv/black)
[![Discord](https://img.shields.io/discord/427417507276783616.svg)](https://discord.gg/Tx9FkEz)
[![Gitlab pipeline status (branch)](https://img.shields.io/gitlab/pipeline/kiwicom/the-zoo/master.svg)](https://gitlab.com/kiwicom/the-zoo/pipelines)

![Service Detail](docs/screenshot-service-details.png)

| What       | Where                                             |
| ---------- | ------------------------------------------------- |
| Discussion | [#the-zoo on Discord](https://discord.gg/Tx9FkEz) |
| Maintainer | [Alex Viscreanu](https://github.com/aexvir/)      |

## What is The Zoo?

A microservice catalogue that allows performing static code checks and integrates with
third party services like Sentry, Datadog or Pingdom.

On top of that we have built a configurable static code analysis module that allows writing
your own code checks and The Zoo will keep track of the evolution of those issues. The checks
can also be integrated in CI so it can show how the Pull Request affects the status of the
issues.

The Zoo also provides analytics about how dependency usage and its versions evolve.

## Development

- Run in debug mode: `$ make run`
- Stop: `$ make stop`
- Stop and/or delete data: `$ make destroy`
- Django shell: `$ make shell`
- Containers logs: `$ docker-compose logs`

Access web locally:

- Web is running on port `20966`
- Login at <http://localhost:20966/admin> with your superuser account
- Access zoo at <http://localhost:20966/>

### Initial setup

- Create a database: `$ make migrate`
- Create a superuser: `$ make superuser`

### Database changes

- Generate database migrations: `$ make makemigrations`
- Update the database when needed: `$ make migrate`

### Notes

Check `Makefile` for shell commands if you want to run them with modified
parameters.

## Testing

Run all tests: `$ make test`

Tests are run by `tox`. In order to run only unit tests or a specific test file
you need to use the `pytest` binary from the `.tox/tests/bin/` folder. This
folder will be created after running tests for the first time.

### Testing requirements

PostgreSQL is needed for running the integration tests, you can install it by
running `brew install postgres`

Note that this includes running `dockerfile_lint` and `remark`, which you can
get with `npm install -g dockerfile_lint remark-cli`.

Also note that tox doesn't know when you change the `requirements.txt`
and won't automatically install new dependencies for test runs.
Run `pip install tox-battery` to install a plugin which fixes this silliness.

If you want to pass some env vars to environment, you can list them in env var
`TOX_TESTENV_PASSENV`. For example if you want to use custom database for tests,
you can run: `TEST_DATABASE_URL=postgres://... TOX_TESTENV_PASSENV=TEST_DATABASE_URL tox`

## Documentation

### Architecture Decision Records

We document architecture decisions like it's described in
[this article](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).

Records are in dir `adr`. We are using [ADR Tools](https://github.com/npryce/adr-tools)
for working with them.

### Documentation for users

We use [Sphinx](http://www.sphinx-doc.org/) for generating documentation. Docs
are in dir `docs`.

Setup virtual enviroment and install there `docs-requirements.txt`. Then you can
use shortcuts:

- Build docs: `$ make build-docs`
- Open docs: `$ make read-docs`
