default: test

test:
    pytest --continue-on-collection-errors -m 'not slow'

test-all:
    pytest --continue-on-collection-errors

coverage:
    pytest --continue-on-collection-errors --cov=src/chimera --cov-branch --cov-report=html -m 'not slow'

coverage-all:
    pytest --continue-on-collection-errors --cov=src/chimera --cov-branch --cov-report=html

