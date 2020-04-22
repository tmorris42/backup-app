ECHO OFF
python -m isort -q --skip .\env\
python -m black -q --line-length 79 backup_app.py
python -m black -q --line-length 79 tests.py
python -m mypy --warn-unused-ignores .
python -m flake8 backup_app.py --ignore E231,E203
python -m flake8 tests.py
python -m pylint backup_app.py
python -m pylint tests.py
python -m pytest -q tests.py
python -m bandit backup_app.py -q
ECHO ON
