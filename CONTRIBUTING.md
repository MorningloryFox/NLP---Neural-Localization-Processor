# Contributing to NLP - Neural Localization Processor

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/NLP---Neural-Localization-Processor.git
   cd NLP---Neural-Localization-Processor
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 conventions
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep lines under 100 characters when possible

### Testing

- Write tests for new features in `tests/`
- Run tests locally before submitting PRs:
  ```bash
  python -m pytest tests/ -v
  ```

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (e.g., "Add", "Fix", "Improve", "Refactor")
- Keep first line under 50 characters
- Add detailed explanation in the body if needed

Example:
```
Add gender-aware translation support

- Implement gender metadata in glossary entries
- Update prompt to enforce gender agreement
- Add tests for pronoun consistency
```

## Submitting a Pull Request

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description of what was changed and why
   - Reference to any related issues
   - Screenshots if UI-related

3. **Review Process**:
   - At least one maintainer review required
   - All CI/CD checks must pass
   - Code coverage should not decrease

## Reporting Issues

When reporting bugs, please include:

- **Description**: Clear, concise explanation of the issue
- **Steps to Reproduce**: Exact steps to trigger the bug
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: Python version, OS, model used
- **Error Messages**: Full error traces if available

Example:
```
**Description**: Translation quality degrades with certain Unicode characters

**Steps to Reproduce**:
1. Create input file with emoji characters
2. Run python main.py
3. Check output

**Expected**: Emojis preserved or gracefully handled
**Actual**: Translation fails with encoding error

**Environment**: Python 3.10, Windows 11, qwen2.5:7b
```

## Feature Requests

When suggesting features, please:

- Explain the use case
- Describe expected behavior
- Provide examples if applicable
- Discuss potential implementation approach

## Areas for Contribution

We're especially interested in:

- **Performance Optimizations**: Faster chunking, caching strategies
- **Quality Improvements**: Better validation metrics, enhanced prompts
- **Language Support**: Additional language-specific features
- **Documentation**: Examples, tutorials, guides
- **Testing**: Unit tests, integration tests, test data
- **UI/Tooling**: Monitoring dashboards, visualization tools
- **Backend Support**: Integration with other LLM providers

## Community Standards

- Be respectful and inclusive
- Provide constructive feedback
- Give credit where credit is due
- Help others learn and grow

## Questions?

- Open a [Discussion](https://github.com/MorningloryFox/NLP---Neural-Localization-Processor/discussions)
- Check [Issues](https://github.com/MorningloryFox/NLP---Neural-Localization-Processor/issues) for similar questions

---

**Thank you for contributing to make NLP better for everyone! ❤️**
