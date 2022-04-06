ECHO OFF
python -m isort -q . --skip .\env\
python -m black -q --line-length 79 backup_app
python -m black -q --line-length 79 tests
python -m mypy --warn-unused-ignores .
python -m flake8 backup_app --ignore E231,E203
python -m flake8 tests
python -m pylint backup_app
python -m pylint tests
python -m pytest -q tests\tests.py
python -m bandit -r -q backup_app
ECHO ON
