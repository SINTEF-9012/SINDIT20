In the pyproject.toml file, update the version number.

# Build and publish to PyPI

## Using uv (recommended)
```bash
# Build the package
uv build

# Upload to PyPI
uv publish
```

## Alternative: Using build + twine
```bash
# Install build tools
uv pip install build twine

# Build the package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

