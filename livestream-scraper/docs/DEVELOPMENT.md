# Development Guide

## Setting Up Development Environment

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/livestream-scraper.git
cd livestream-scraper
```

### 2. Install Dev Dependencies

```bash
pip install -r requirements.txt
pip install pytest black flake8 mypy
```

### 3. Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## Project Structure

```
livestream-scraper/
├── src/                 # Source code
├── tests/              # Test files
├── docs/               # Documentation
├── config/             # Configuration templates
├── examples/           # Example scripts
├── requirements.txt    # Dependencies
└── setup.py           # Package setup
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Docstrings for all public functions/classes

### Example

```python
def extract_phones(text: str, context: Optional[str] = None) -> List[PhoneNumber]:
    """
    Extract phone numbers from text.
    
    Args:
        text: Text to search
        context: Optional context for the phone number
        
    Returns:
        List of PhoneNumber objects
    """
    # Implementation
    pass
```

## Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src

# Specific test
pytest tests/test_extractor.py
```

### Writing Tests

```python
# tests/test_extractor.py
import pytest
from src.extractor import PhoneExtractor

def test_extract_chinese_mobile():
    extractor = PhoneExtractor([
        {'name': 'china', 'pattern': r'1[3-9]\d{9}', 'enabled': True}
    ])
    
    phones = extractor.extract("Call 13800138000")
    assert len(phones) == 1
    assert phones[0].raw == "13800138000"
```

## Contributing Workflow

### 1. Create Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code
- Add tests
- Update documentation

### 3. Run Quality Checks

```bash
# Formatting
black src/

# Linting
flake8 src/

# Type checking
mypy src/

# Tests
pytest
```

### 4. Commit

```bash
git add .
git commit -m "feat: add feature description"
```

### Commit Message Format

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `perf:` Performance improvement

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Adding New Features

### Adding a New Extractor Pattern

1. Edit `src/extractor.py`
2. Add pattern to default patterns
3. Add test case
4. Update documentation

### Adding Output Format

1. Edit `src/writer.py`
2. Add write method
3. Update config schema
4. Add tests

### Adding Platform Support

1. Create platform-specific scraper in `src/platforms/`
2. Inherit from base `LiveStreamScraper`
3. Override necessary methods
4. Add example config

## Release Process

1. Update version in `src/__init__.py`
2. Update CHANGELOG.md
3. Create git tag
4. Build package
5. Push to PyPI (maintainers only)

## Getting Help

- Open an issue for bugs
- Start a discussion for features
- Join our Discord (if available)

## Code of Conduct

- Be respectful
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints
