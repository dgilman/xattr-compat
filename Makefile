BLACK_FILES=*.py tests/*.py xattr_compat/*.py

format:
	isort --profile black  $(BLACK_FILES)
	black $(BLACK_FILES)

format-check:
	isort --check --profile black  $(BLACK_FILES)
	black --check $(BLACK_FILES)

