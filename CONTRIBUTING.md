# Contributing to Zen Downloader

Thank you for your interest in contributing to Zen Downloader! This document outlines the process for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating a bug report:
1. Check the [FAQ section](README.md#faq) in README
2. Search existing issues to avoid duplicates
3. Use the bug report template when creating an issue

### 💡 Suggesting Features

We welcome new feature ideas! Please:
1. Check if the feature already exists
2. Describe the problem you're trying to solve
3. Explain why this feature would be valuable

### 📝 Improving Documentation

Good documentation is essential! You can help by:
- Fixing typos or grammar errors
- Adding examples to existing documentation
- Creating new guides or tutorials

### 💻 Submitting Code Changes

#### Prerequisites

- Python 3.10+
- FFmpeg installed
- Git installed

#### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Zen-Downloader.git
   cd Zen-Downloader
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Coding Standards

- Use meaningful variable and function names
- Add comments for complex logic
- Follow PEP 8 style guide
- Test your changes locally before submitting

#### Submitting Your Changes

1. Commit your changes:
   ```bash
   git add .
   git commit -m "Add: description of your changes"
   ```

2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a Pull Request

#### Pull Request Guidelines

- Fill in the required PR template
- Link any related issues
- Include screenshots for UI changes
- Ensure all tests pass

## Project Structure

```
Zen-Downloader/
├── app.py              # Main Flask application
├── run.bat             # One-click launcher
├── setup.bat           # Setup script
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/           # Stylesheets
│   └── js/            # Frontend JavaScript
└── templates/
    └── index.html     # Main HTML template
```

## Getting Help

- Open an [Issue](https://github.com/henglyrepo/Zen-Downloader/issues)
- Check the [FAQ](README.md#faq) in README

---

Thank you for contributing! 🎉
