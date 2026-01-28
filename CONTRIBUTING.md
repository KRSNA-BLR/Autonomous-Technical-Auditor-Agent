# Contributing to Autonomous Tech Research Agent

First off, thank you for considering contributing! 🎉

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in [Issues](https://github.com/yourusername/autonomous-tech-research-agent/issues)
- If not, create a new issue with:
  - Clear title and description
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (OS, Python version)

### Suggesting Features

- Open an issue with the `enhancement` label
- Describe the feature and its use case
- Explain why it would be valuable

### Pull Requests

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** following our coding standards
5. **Run tests** to ensure nothing is broken:
   ```bash
   make check  # Runs format, lint, typecheck, test
   ```
6. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add amazing new feature"
   ```
7. **Push** to your fork and create a **Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/autonomous-tech-research-agent.git
cd autonomous-tech-research-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dev dependencies
make setup

# Copy environment file
cp .env.example .env
# Add your GROQ_API_KEY
```

## Coding Standards

- **Python 3.11+** with type hints
- **Formatting**: `ruff format`
- **Linting**: `ruff check`
- **Type checking**: `mypy` (strict mode)
- **Testing**: `pytest` with good coverage

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: bug fix
docs: documentation changes
style: formatting, no code change
refactor: code restructuring
test: adding tests
chore: maintenance tasks
```

## Architecture Guidelines

- Follow **Hexagonal Architecture** principles
- Domain entities must be **pure Python** (no external dependencies)
- Use **dependency injection** for external services
- Write **tests** for new functionality

## Questions?

Feel free to open an issue or discussion!

---

Thank you for contributing! 🙌
