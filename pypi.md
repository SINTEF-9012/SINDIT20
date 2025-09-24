In the pyproject.toml file, set package-mode = true, and update version.

# Build and publish to PyPI
poetry build
python3 -m twine upload  dist/*
