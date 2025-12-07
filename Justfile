package := 'messagebus'
default_test_suite := 'tests'

install:
    uv sync --group dev --group doc

doc:
    cd docs && uv run make html
    xdg-open docs/build/html/index.html

cleandoc:
    cd docs && uv run make clean

gensync: && fmt
    uv run python scripts/gen_unasync.py

test: gensync typecheck lint unittest

lf:
    uv run pytest -sxvvv --lf

unittest test_suite=default_test_suite:
    uv run pytest -sxv {{test_suite}}

lint:
    uv run ruff check .

fmt:
    uv run ruff check --fix .
    uv run ruff format src tests

black: fmt
    echo "$(tput setaf 3)Warning: Use 'just fmt' instead$(tput setaf 7)"

typecheck:
    uv run mypy src/messagebus/ tests/

cov test_suite=default_test_suite:
    rm -f .coverage
    rm -rf htmlcov
    uv run pytest --cov-report=html --cov={{package}} {{test_suite}}
    xdg-open htmlcov/index.html

release major_minor_patch: gensync test && changelog
    uvx --with=pdm,pdm-bump --python-preference system pdm bump {{major_minor_patch}}
    uv sync --group dev --frozen


changelog:
    uv run python scripts/write_changelog.py
    cat CHANGELOG.rst >> CHANGELOG.rst.new
    rm CHANGELOG.rst
    mv CHANGELOG.rst.new CHANGELOG.rst
    $EDITOR CHANGELOG.rst

publish:
    git commit -am "Release $(uv run scripts/get_version.py)"
    git push
    git tag "v$(uv run scripts/get_version.py)"
    git push origin "v$(uv run scripts/get_version.py)"
