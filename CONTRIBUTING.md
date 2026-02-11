# Contributing to Sensor Community Analytics

Thank you for your interest in contributing to Sensor Community Analytics! We welcome contributions from the community and are excited to have you here.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

---

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

### Our Standards

**Examples of behavior that contributes to a positive environment:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior:**
- The use of sexualized language or imagery and unwelcome sexual attention
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

**Bug Report Template:**

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. Ubuntu 22.04]
 - Python Version: [e.g. 3.10.5]
 - Django Version: [e.g. 4.2.0]
 - Browser: [e.g. Chrome 120]

**Additional context**
Add any other context about the problem here.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful** to most users
- **List some examples** of how this feature would be used
- **Specify which version** you're using

### Your First Code Contribution

Unsure where to begin? You can start by looking through these issues:

- **Good First Issue** - issues that are good for newcomers
- **Help Wanted** - issues that need assistance
- **Documentation** - improvements or additions to documentation
- **Bug Fixes** - small bug fixes that are well-defined

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following our coding standards
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

**Pull Request Template:**

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran and how to reproduce them.

## Checklist
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Screenshots (if applicable)
Add screenshots to demonstrate the changes.

## Related Issues
Fixes #(issue number)
```

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Git
- A PostgreSQL client (optional, for database inspection)

### Initial Setup

1. **Fork and Clone the Repository**

```bash
git clone https://github.com/YOUR_USERNAME/sensor-community-analytics.git
cd sensor-community-analytics
```

2. **Create a Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Start Docker Services**

```bash
docker-compose up -d
```

5. **Set Up Environment Variables**

```bash
cp env-sample .env
# Edit .env with your configuration
```

6. **Run Migrations**

```bash
python manage.py migrate
python manage.py load_sensor_type
```

7. **Create a Superuser**

```bash
python manage.py createsuperuser
```

8. **Run the Development Server**

```bash
python manage.py runserver
```

### Making Changes

1. **Create a new branch** for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

2. **Make your changes** and commit them with descriptive messages

3. **Push to your fork**:

```bash
git push origin feature/your-feature-name
```

4. **Open a Pull Request** from your branch to our `main` branch

---

## Coding Standards

### Python Code Style

We follow **PEP 8** style guidelines for Python code:

- Use 4 spaces for indentation (no tabs)
- Maximum line length of 120 characters
- Use descriptive variable names
- Add docstrings to all functions, classes, and modules
- Use type hints where appropriate

**Example:**

```python
from typing import List, Optional
from django.db import models

class Station(models.Model):
    """
    Represents a physical monitoring station location.
    
    Attributes:
        name: Human-readable name for the station
        latitude: Geographic latitude coordinate
        longitude: Geographic longitude coordinate
    """
    name = models.CharField(max_length=255, help_text="Station name")
    latitude = models.FloatField(help_text="Latitude coordinate")
    longitude = models.FloatField(help_text="Longitude coordinate")
    
    def get_sensors(self) -> List['Sensor']:
        """
        Retrieve all sensors associated with this station.
        
        Returns:
            List of Sensor objects attached to this station
        """
        return self.sensor_set.all()
```

### Django Best Practices

- **Models**: Keep models focused and single-purpose
- **Views**: Use class-based views when appropriate
- **Templates**: Follow DRY principles, use template inheritance
- **URLs**: Use meaningful URL patterns with named URLs
- **Forms**: Use Django forms for all user input validation
- **Security**: Never commit secrets, use environment variables

### JavaScript Code Style

- Use modern ES6+ syntax
- Use `const` and `let`, avoid `var`
- Use meaningful variable names
- Add comments for complex logic
- Format code consistently

**Example:**

```javascript
// Good
const fetchSensorData = async (sensorId, startDate, endDate) => {
    try {
        const response = await fetch(`/api/sensors/${sensorId}/data`, {
            method: 'POST',
            body: JSON.stringify({ startDate, endDate })
        });
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch sensor data:', error);
        throw error;
    }
};

// Avoid
var x = function(a, b, c) {
    return a + b + c;
};
```

### HTML/CSS Standards

- Use semantic HTML5 elements
- Follow BEM naming convention for CSS classes
- Ensure accessibility (ARIA labels, alt text, etc.)
- Use Tailwind CSS utility classes when appropriate
- Maintain responsive design principles

---

## Commit Messages

Write clear, descriptive commit messages following these guidelines:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without feature changes
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependency updates

### Examples

**Good:**
```
feat(sensor): add support for DHT22 temperature sensors

- Add DHT22 to supported sensor types
- Update sensor detection logic
- Add migration for new sensor type

Closes #123
```

**Good:**
```
fix(download): resolve timeout issue for large date ranges

The download process was timing out for requests spanning more than
30 days. Implemented chunked downloads to process data in smaller
batches.

Fixes #456
```

**Avoid:**
```
fixed stuff
update
changes
```

---

## Testing Guidelines

### Writing Tests

- Write tests for all new features
- Update tests when modifying existing code
- Aim for high code coverage (target: 80%+)
- Use descriptive test names
---

## Documentation

### Code Documentation

- Add docstrings to all functions, classes, and modules
- Use Google-style or NumPy-style docstrings
- Document function parameters and return values
- Include usage examples in docstrings

### README Updates

When adding new features:
- Update the README.md with usage instructions
- Add examples and code snippets
- Update the feature list
- Add troubleshooting notes if applicable

### Inline Comments

- Use comments to explain **why**, not **what**
- Keep comments up-to-date with code changes
- Remove commented-out code before committing

**Good:**
```python
# Check sensor availability before download to avoid wasting API calls
if not sensor.is_active:
    return None
```

**Avoid:**
```python
# Set x to 5
x = 5
```

---

## Community

### Getting Help

- **GitHub Discussions**: Ask questions and share ideas
- **Issues**: Report bugs and request features
- **Email**: Contact maintainers directly (see README)

### Recognizing Contributors

We value all contributions! Contributors will be:
- Listed in the project's contributors page
- Mentioned in release notes for significant contributions
- Invited to join the maintainers team for sustained contributions

### Communication Guidelines

- Be respectful and constructive
- Stay on topic
- Help others when you can
- Ask questions if something is unclear
- Provide context when asking for help

---

## Review Process

### What to Expect

1. **Initial Review**: A maintainer will review your PR within 1-2 weeks
2. **Feedback**: You may receive requests for changes or clarification
3. **Iteration**: Make requested changes and push updates
4. **Approval**: Once approved, a maintainer will merge your PR
5. **Release**: Your changes will be included in the next release

### Review Criteria

Pull requests are evaluated based on:
- **Code Quality**: Follows coding standards and best practices
- **Testing**: Includes appropriate tests with good coverage
- **Documentation**: Code is well-documented
- **Functionality**: Works as intended without breaking existing features
- **Performance**: Doesn't introduce significant performance issues
- **Security**: No security vulnerabilities introduced

---

## License

By contributing to Sensor Community Analytics, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

Don't hesitate to ask questions! We're here to help. Open an issue labeled "question" or reach out to the maintainers.

**Thank you for contributing to Sensor Community Analytics!** 🎉

---

**Last Updated**: February 2026