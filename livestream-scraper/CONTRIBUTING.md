# Contributing to LiveStream Phone Extractor

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Welcome newcomers
- Respect different viewpoints and experiences

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported
2. Open a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, etc.)
   - Error messages and logs

### Suggesting Features

1. Open an issue with the "feature request" label
2. Describe the feature and its use case
3. Explain why it would be useful

### Pull Requests

1. **Fork** the repository
2. **Create a branch** for your feature (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Run tests** (`pytest`)
5. **Update documentation** if needed
6. **Commit** with clear messages
7. **Push** to your fork
8. **Open a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/livestream-scraper.git
cd livestream-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dev dependencies
pip install -r requirements.txt
pip install black flake8 mypy pytest pytest-cov

# Install pre-commit hooks
pre-commit install
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100
- Use descriptive variable names

### Docstrings

Use Google-style docstrings:

```python
def extract_phones(text: str, context: Optional[str] = None) -> List[PhoneNumber]:
    """
    Extract phone numbers from text.
    
    Args:
        text: Text to search
        context: Optional context for the phone number
        
    Returns:
        List of PhoneNumber objects
        
    Raises:
        ValueError: If text is invalid
    """
```

### Testing

- Write tests for new features
- Maintain coverage above 80%
- Use pytest

```bash
# Run tests
pytest

# With coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

## Commit Message Format

Use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

Example:
```
feat: add support for UK phone numbers

- Add UK phone pattern
- Update validation logic
- Add tests
```

## Pull Request Process

1. Update README.md if needed
2. Update CHANGELOG.md
3. Ensure all tests pass
4. Request review from maintainers
5. Address review comments
6. Maintainers will merge once approved

## Questions?

- Open a discussion for general questions
- Join our community chat (if available)
- Email maintainers (for sensitive issues)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing! 🎉
