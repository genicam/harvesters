# Harvesters Contribution

Dear Contributors,

Thank you for taking the time for Harvester. Please feel free to create a pull request when you get an idea.
A short introduction to the build and test environment is described bellow.

Best regards,
Silvan

## Development Setup

There are several ways to install Python. You can choose your preferred way.
The only requirement is, an actual Python Version according to https://devguide.python.org/versions/

The Harvesters Project contains a `pyproject.toml` including the declaration of 
all runtime and build dependencies.
It is recommended to setup a dedicated Python environment for the development.
This section describes the usage of `venv` and `pip`.

1. Setup or activate your preferred Python interpreter 
2. Switch to the project (harvesters) directory
3. Create a new _virtual envionment_: `python -m venv .venv`
4. Activate the environment `.venv\Script\activate` or `source .venv/bin/activate`
5. Ensure that you have an actual version of pip (>=25.1.1)
6. Install runtime development version of _Harvesters_ and dependencies  `pip install -e .`
7. Install test and build dependencies `pip install --group dev`

## Project Tests

There is a small GenTL producer included in the _genicam_ package.
It is used for a basic test of the _Harvesters_ core.

1. Run `pytest` in your Python environment on the top-level directory.

