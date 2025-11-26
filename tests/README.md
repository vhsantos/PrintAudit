# PrintAudit Tests

This directory contains the test suite for PrintAudit.

## Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run with coverage
pytest --cov=printaudit

# Run specific test file
pytest tests/test_config.py
```

## Test Structure

- `test_*.py` - Unit tests for individual modules
- `test_integration_*.py` - Integration tests (marked with `@pytest.mark.integration`)
