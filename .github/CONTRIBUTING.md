# Contributing to BusinessPilot AI

Thank you for considering contributing to BusinessPilot AI! Contributions are what make the open-source community an amazing place to learn, inspire, and create.

## Code of Conduct
By participating in this project, you agree to abide by our Code of Conduct: be respectful, professional, constructive, and helpful at all times.

## How Can I Contribute?

### Reporting Bugs
- Search existing issues to see if the bug has already been reported.
- If not, open a new issue using our Bug Report template, providing detailed environment details and reproduction steps.

### Suggesting Enhancements
- Open a new issue using our Feature Request template, explaining the proposed behavior and business value.

### Pull Requests
1. Fork the repository and create your branch from `main`.
2. Ensure you add unit tests for any scoring or orchestrator logic enhancements.
3. Keep the dashboard components modular and clean.
4. Run the local verification checks before committing:
   ```bash
   python verify_requirements.py
   pytest tests/
   ```
5. Submit your PR with a completed pull request template.

## Coding Style
- Follow standard Python PEP 8 style guidelines.
- Include docstrings and comments for all new agents, tools, or helpers.
