# Publishing to PyPI

This guide explains how to publish `odoo-index-mcp` to PyPI so users can install it with `uvx` or `pip`.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [TestPyPI](https://test.pypi.org/account/register/) (testing)

2. **API Tokens**: Generate API tokens for both:
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/

   Save these tokens securely - you'll need them for publishing.

3. **Install build tools**:
   ```bash
   uv tool install build
   uv tool install twine
   ```

## Before Publishing

### 1. Update Author Information

Edit `pyproject.toml` and replace the placeholder author info:

```toml
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
```

### 2. Version Bump

Update the version in `pyproject.toml`:

```toml
version = "0.1.0"  # Change as needed
```

### 3. Update CHANGELOG

Document changes in a CHANGELOG.md file (create if needed).

### 4. Test Locally

```bash
# Run your CLI tool
uv run python cli.py --stats

# Start the MCP server
uv run odoo-index-mcp
```

## Building the Package

```bash
# Clean any previous builds
rm -rf dist/ build/ *.egg-info

# Build the package
uv build

# Or using python -m build
python -m build
```

This creates two files in the `dist/` directory:
- `odoo_index_mcp-0.1.0.tar.gz` (source distribution)
- `odoo_index_mcp-0.1.0-py3-none-any.whl` (wheel distribution)

## Publishing

### Test on TestPyPI First

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# You'll be prompted for:
# Username: __token__
# Password: <your TestPyPI API token>
```

### Test the TestPyPI Package

```bash
# Test installation from TestPyPI
uvx --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple \
    odoo-index-mcp --help
```

### Publish to PyPI

Once tested, publish to the real PyPI:

```bash
# Upload to PyPI
twine upload dist/*

# You'll be prompted for:
# Username: __token__
# Password: <your PyPI API token>
```

## After Publishing

### Test Installation

```bash
# Run without installing (like npx)
uvx odoo-index-mcp --help

# Or install globally
uv tool install odoo-index-mcp

# Or with pip
pip install odoo-index-mcp
```

### Update README

Add installation instructions to README.md:

```markdown
## Installation

### Quick Start (No Installation Required)

Run directly with uvx (like npx for Python):

```bash
# Run the MCP server
uvx odoo-index-mcp

# Run the CLI tool
uvx --from odoo-index-mcp odoo-index-cli --help
```

### Install Globally

```bash
# Using uv
uv tool install odoo-index-mcp

# Using pipx
pipx install odoo-index-mcp

# Using pip
pip install odoo-index-mcp
```

### Git Tag the Release

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Automation with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install build tools
        run: |
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add your PyPI API token to GitHub Secrets:
- Go to: Settings → Secrets and variables → Actions
- Add new secret: `PYPI_API_TOKEN`

## Troubleshooting

### "File already exists" error

PyPI doesn't allow re-uploading the same version. You must bump the version number in `pyproject.toml`.

### Import errors after installation

Make sure your package structure is correct:
```
odoo_index_mcp/
├── __init__.py
├── server.py
└── ...
```

### Missing dependencies

Ensure all dependencies are listed in `pyproject.toml` under `dependencies`.

### CLI scripts not working

Verify the entry points in `pyproject.toml`:
```toml
[project.scripts]
odoo-index-mcp = "odoo_index_mcp.server:main"
odoo-index-cli = "cli:main"
```

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [uv Documentation](https://docs.astral.sh/uv/)
