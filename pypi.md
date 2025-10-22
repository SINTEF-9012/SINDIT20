In the pyproject.toml file, set package-mode = true, and update version.

# Build and publish to PyPI
poetry build
python -m twine upload  dist/*
