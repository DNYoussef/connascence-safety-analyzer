# Contributing to Connascence Safety Analyzer

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Node.js 16.x or higher
- VS Code 1.74.0 or higher
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/DNYoussef/connascence-safety-analyzer.git
   cd connascence-safety-analyzer
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Open in VS Code**
   ```bash
   code .
   ```

4. **Run the extension**
   - Press `F5` to launch a new Extension Development Host
   - Test your changes in the new VS Code window

## 🏗️ Project Structure

```
vscode-extension/
├── src/
│   ├── core/           # Main extension logic
│   ├── providers/      # Language service providers
│   ├── services/       # Business logic services
│   ├── ui/            # User interface components
│   └── utils/         # Utility functions
├── package.json       # Extension manifest
└── README.md
```

## 🧪 Testing

### Manual Testing
1. Install the extension in development mode (`F5`)
2. Open test files in supported languages (Python, JS, TS, C, C++)
3. Verify violations are detected and highlighted
4. Test hover tooltips and AI suggestions
5. Check dashboard functionality

### Automated Tests
```bash
npm run test
```

## 📝 Code Style

- Use TypeScript for all new code
- Follow existing naming conventions
- Add JSDoc comments for public APIs
- Use consistent indentation (2 spaces)
- Run `npm run lint` before committing

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Information**
   - VS Code version
   - Extension version
   - Operating system

2. **Steps to Reproduce**
   - Clear, numbered steps
   - Sample code that triggers the bug
   - Expected vs actual behavior

3. **Screenshots/Videos** (if applicable)

## 💡 Feature Requests

For new features:

1. Check if the feature already exists
2. Provide a clear use case
3. Explain the expected behavior
4. Consider implementation complexity

## 🔀 Pull Request Process

1. **Fork and Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Keep commits focused and atomic
   - Write descriptive commit messages
   - Follow the existing code style

3. **Test Thoroughly**
   - Test your changes manually
   - Ensure no regressions
   - Add tests for new functionality

4. **Submit PR**
   - Provide a clear description
   - Reference related issues
   - Include screenshots for UI changes

## 🏆 Recognition

Contributors will be:
- Listed in the CHANGELOG
- Mentioned in release notes
- Added to the contributors section

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Discord**: Join our community server (link in README)

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

Thank you for contributing to making code analysis better for everyone! 🎉