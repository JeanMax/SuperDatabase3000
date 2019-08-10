
# Customize this!
NAME = superdatabase3000
AUTHOR = JeanMax
VERSION = 0.1


# Some globads
SRC_DIR = src
TEST_DIR = tests
DOC_DIR = docs
DOC_BUILD_DIR = docs/_build

TMP_FILES = build dist temp $(DOC_DIR) .coverage .pytest_cache \
			$(shell find . -name __pycache__) \
			$(shell find . -name '*.egg-info') \
RM = rm -rfv

SPHINX = sphinx-build -D "autodoc_mock_imports=torch"
TESTER = setup.py --quiet test --addopts --fulltrace --addopts --quiet
FLAKE = flake8
LINTER = pylint --rcfile=setup.cfg $(shell if [ "$(TERM)" = dumb ]; then echo "-fparseable"; fi)
PIP_INSTALL = pip install $(shell test "$EUID" = 0 || echo "--user")
PIP_UNINSTALL = pip uninstall -y


# INSTALL
$(NAME): install_dev

install:
	$(PIP_INSTALL) .

install_dev:
	$(PIP_INSTALL) .[dev]
	$(PIP_INSTALL) --editable .

clean:
	$(RM) $(TMP_FILES)

uninstall: clean
	$(PIP_UNINSTALL) $(NAME)

reinstall: uninstall
	$(MAKE) $(NAME)


# LINT && TEST
lint:
	find $(SRC_DIR) -name \*.py | grep -vE '\.#|flycheck_|eggs' | xargs $(LINTER)

flake:
	$(FLAKE)

test:
	python3 $(TESTER)

coverage:
	coverage run --source=$(SRC_DIR) $(TESTER)
	coverage report --omit '*__init__.py' --fail-under 90 -m

todo:
	! grep -rin todo . | grep -vE '^(Binary file|\./\.git|\./Makefile|\./docs|\./setup.py|\.egg)'

check: lint flake coverage todo


# DOC
$(DOC_BUILD_DIR):
	sphinx-apidoc --ext-viewcode -H $(NAME) -A $(AUTHOR) -V $(VERSION) -F -o $(DOC_DIR) $(SRC_DIR)/$(NAME)

html: $(DOC_BUILD_DIR)
	$(SPHINX) -b html $(DOC_DIR) $(DOC_BUILD_DIR)

man: $(DOC_BUILD_DIR)
	$(SPHINX) -b man $(DOC_DIR) $(DOC_BUILD_DIR)

doc: html man


# Avoid collisions between rules and files
.PHONY: $(NAME), install, install_dev, clean, uninstall, reinstall, \
		lint, flake, test, coverage, check, todo, \
		$(DOC_BUILD_DIR), html, man, doc
