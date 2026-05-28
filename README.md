# Plone Badisblocks

Rendering blocks in Badis UI with Chameleon

## Features

- Compatible with Plone 6.2+

## Installation

Add `plone.badisblocks` to your project's dependencies:

```python
# In your pyproject.toml
dependencies = [
    "plone.badisblocks",
    # ...
]
```

Then activate the addon in your Plone site's control panel or via GenericSetup.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/collective/plone.badisblocks.git
cd plone.badisblocks

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[test]"
```

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=plone.badisblocks --cov-report=html
```

## License

GPL-2.0-or-later

## Author

Maik Derstappen <md@derico.de>
