# Assumptions on the system and the application packager

These are some assumptions about the host system and/or the application packaging:
1. The app was developed and tested on Windows without Docker since I don't have a Linux machine and/or virtualization available. Hope all works as expected 🙂
2. The system expects some system-level dependency such as the Python manager `uv` to be available. If this is not the case, the installation tutorial is trivial, e.g. just download its binary with `curl` and install it with `sh` (on your expected Linux platform):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    For more information, please see: https://docs.astral.sh/uv/getting-started/installation/

3. `uv` uses the `pyproject.toml` file to sync project dependencies and the `uv.lock` file to replicate the project environment with locked version dependencies depending on the given platform. Please, just delete the `uv.lock` file before running the `uv sync` command to replicate the project dependencies when following the "How to run the project" steps.\
<u>The `uv.lock` was commited into the git repository to have a replicable Windows installation, if needed.</u>

# Design decisions and feedback
These are notes about the design decisions of the project, and challenges and feedback during the development:
1. FastAPI Python backend server with Pydantic models for the APIs input and output schemas when needed for the validation.
2. The auth functional requirements was developed with the `pwdlib[argon2]` and `pyjwt` libraries. The design was inspired by FastAPI tutorials (easy and advance) on security with a simple approach where the security is centralized by means of depedency injection on the APIs endpoints.
I tried out implementing the roles to authenticate the private users APIs and private manager APIs by means of comparing requested scopes from the third party token provider (here FastAPI \token endpoint) vs available scopes associated with users (e.g. read from an application database). The approach seems working nice and seems scalable. The storage of data for the auth (e.g. registered users) is an hardcoded in-memory python dict to mock the database.
2. SQLModel to try out the integration between the ORM of SQLAlchemy with Pydantic models into FastAPI: I found out the library is not actively developed and is not well document. A raw SQLAlchemy ORM o Core approach would have been smoother. The data model is simple with a table for the measurements and a table for the components, and a third table for the report service. The domain model instead uses Pydantic models to exploits the information based on the domain functional requirements. Here again dependency injection was tried out to integrate the database layer into FastAPI endpoints to drive a centralized approach to manage the engine, connection, and sessions of the database.
3. The report generation was designed with an sync background task exploiting FastAPI features. Since the report generation is expected to be CPU-bounded for the local KPI computation, the task is sync so that FastAPI create a new thread where the computation takes place without blocking the main server loop.
Another approach would be to make the SQL query more complex and run the computation on the database server, consuming more resourced there. In this case the task could be IO-bounded due to the delay to get the response from the database and the task could be made async with the promise not to be blocking.
A more structured approach would be to spawn direcly a new process with multiprocessing or using an infrastructure approach where a new worker is spawn to compute the report, e.g. with Kubernetes cluster and Celery library, for instance.
4. Code quality complaince is ensure using modern python tools such as `ruff` linter and formatter. The codebase was type-hinted and checked statically with the new tool `pyrefly`: it is very fast compared to `pyright`, so it feels right during development. `pyright` could be added later on to compare the results of two type checkers.
5. Tests are organised by their type with the following folder structure:
    - tests/unit/ - Isolated unit tests that test the behaviour of a single unit. The idea is that collaborators should be mocked. No database or network access is permitted.

    - tests/integration/ - For testing several units and how they are plumbed together. These often require database access and use factories for set-up. These are best avoided in favour or isolated unit tests (to drive design) and end-to-end functional tests (to know things work as expected at night).

    - tests/functional/ - For end-to-end tests designed to check everything is plumbed together correctly. The ideas is that these should use FastAPI test client to trigger the test and only patch third party calls
6. The storage of data for the domain is an application database. SQLite was chosen to try out this file database. It was fun but tricky w.r.t. supported features and performance: e.g. the integration with async code from FastAPI and the managements of different connections/drivers accessing the database at the same time (e.g. the SQLModel ORM or a low-level adbc/connectorx driver from Polars).
The size and the temporal data suggests that another production-level database with suitable plugins could be more suitable: e.g. a temporal database or a lakehouse based on columnar datastore such as query manager on top of Apache Parquet.

TD;DR: Overall the test was fun and I tried out new technologies for this project

# Next Steps
These are notes about next steps to take:
1. Logging code to understand the workflow and use the logging utilities to save logs both to sdout and to file.
2. Design and gather together proper domain exceptions and HTTP exceptions in order to be consistent. Unit test them.
3. Refactor code into a more consistent DDD structure with design patterns, use TDD to drive design.

# How to run the project with a local deployment
Inside the root folder, sync the Python application project dependencies by running:
```cmd
uv sync
```

Ensure the Python virtual enviroment interpreter of the project (saved in the hidden [.venv](.venv) folder) is activated on the terminal. Then, you can run one of the following options:
1. Use the `VSCode` debugger: just run the VSCode runner/debugger on the [src/main.py](src/main.py). The launch configuration of VSCode are commited in the .git repo.

2. Use the `uv` utility to run the entrypoint file:
    ```cmd
    uv run src/main.py
    ```
3. Use the `docker` utility to build and start a container on the host system:
    ```cmd
    make docker-build
    make docker-run
    ```
## Local Tester/Frontend site
Once the server is running, you can nagigate to the docs page [http://127.0.0.1:8080/b/docs](http://127.0.0.1:8080/b/docs) to trigger the APIs and validate a preferred workflow. The idea is to authorize into the system by clicking the authorize button in top-right corner with these credentials:
- username: `user`, password: `user`
- username: `manager`, password: `manager`

The user `user` can only request and obtain the `user` scope, while the `manager` user can obtain either the `user` or the `manager` or both the scopes.

# Development tools and commands
The `uv` utility is used to install and use project tools as well. See the following examples of available operations. These operations are saved in the [makefile](makefile) file as well.

To run the helper utility and see available commands, run:
```cmd
make help
```
Then you can run them with `make`. Otherwise you can run them directly too as follows:

To run the ruff linter to perform checks, run:
```cmd
uv run ruff check . --fix
```
To run the ruff formatter, run:
```cmd
uv run ruff format .
```
To run the pyright type-hints analysis on static files, run:
```cmd
uv run pyrefly check .
```
To run the pytest suite case of unit tests, run:
```cmd
uv run pytest tests/unit -v
```
To run the pytest suite case of functional tests, run:
```cmd
uv run pytest tests/functional -v
```
To run the pytest suite case with all the tests and stoud captured, run:
```cmd
uv run pytest -v -s
```
# Validation
A production database was created using the [tests\conftest.py](tests\conftest.py) testing utility by changing:
```python
NUM_COMPONENTS = 100
NUM_MEASUREMENTS = 30000
```
And without removing the database after yielding the fixture:
```python
    # Cleanup after all tests
    engine.dispose()
    # db_path = settings.URI.replace("sqlite:///", "")
    # if os.path.exists(db_path):
    #    os.remove(db_path)
    #    logger.info(f"Removed test database: {db_path}")
```
The database creation process took around 5 - 10 minutes on my machine.

Next, this database can be renamed\moved to `database.db` to be used in the deployed application to test the API using at least 100 components and 10000 measurements (per component) and generating report over different periods as requested from [python_esercise.md](python_esercise.md) 