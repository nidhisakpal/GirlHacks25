# Contributing to Gaia Mentorship

Thank you for your interest in contributing to Gaia! This document provides guidelines for contributing to the project.

## Code of Conduct

This project follows a code of conduct that ensures a welcoming environment for all contributors. Please be respectful and inclusive in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Follow the setup guide in `docs/SETUP_GUIDE.md`
4. Create a new branch for your feature/fix

## Development Workflow

### Branch Naming
- `feature/description` - for new features
- `fix/description` - for bug fixes
- `docs/description` - for documentation updates
- `refactor/description` - for code refactoring

### Commit Messages
Use clear, descriptive commit messages:
```
feat: add new goddess persona Artemis
fix: resolve authentication token validation issue
docs: update API documentation
refactor: improve goddess matching algorithm
```

## Code Standards

### Frontend (React/TypeScript)
- Use TypeScript for all components
- Follow React best practices (hooks, functional components)
- Use Tailwind CSS for styling
- Maintain consistent component structure
- Add proper error boundaries and loading states

### Backend (Python/FastAPI)
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Add comprehensive docstrings
- Implement proper error handling
- Use async/await for I/O operations

### General
- Write clear, self-documenting code
- Add comments for complex logic
- Follow existing naming conventions
- Keep functions small and focused
- Write tests for new functionality

## Testing

### Frontend Testing
```bash
cd frontend
npm run test
```

### Backend Testing
```bash
cd backend
pytest
```

### Integration Testing
Test the full flow:
1. User authentication
2. Goddess matching
3. Chat functionality
4. Resource retrieval

## Pull Request Process

1. **Create a Pull Request** with a clear description
2. **Link Issues** - reference any related issues
3. **Add Tests** - include tests for new functionality
4. **Update Documentation** - update relevant docs
5. **Request Review** - ask team members to review

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tests pass locally
- [ ] Manual testing completed
- [ ] Integration testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

## Areas for Contribution

### High Priority
- **New Goddess Personas**: Add more goddesses with unique personalities
- **Data Sources**: Expand scraping to more NJIT resources
- **UI/UX Improvements**: Enhance the chat interface
- **Performance Optimization**: Improve response times
- **Error Handling**: Better error messages and recovery

### Medium Priority
- **Analytics**: Add usage tracking and insights
- **Personalization**: User preferences and history
- **Mobile Support**: Responsive design improvements
- **Accessibility**: WCAG compliance improvements
- **Internationalization**: Multi-language support

### Low Priority
- **Advanced AI Features**: More sophisticated responses
- **Gamification**: Achievement system
- **Social Features**: User interactions
- **Admin Dashboard**: Management interface
- **API Extensions**: Additional endpoints

## Goddess Persona Guidelines

When adding new goddesses:

1. **Research**: Study the goddess's mythology and attributes
2. **Keywords**: Define relevant keywords for matching
3. **Personality**: Create consistent personality traits
4. **Response Style**: Develop unique voice and tone
5. **Domain**: Clearly define their area of expertise

Example goddess configuration:
```python
"artemis": {
    "keywords": [
        "independence", "nature", "wilderness", "hunting", "archery",
        "self-reliance", "outdoor", "adventure", "freedom"
    ],
    "personality_traits": [
        "independent", "fierce", "protective", "wild", "determined",
        "self-sufficient", "adventurous", "strong-willed"
    ]
}
```

## Data Source Guidelines

When adding new data sources:

1. **Respect robots.txt** and rate limits
2. **Handle errors gracefully** with fallbacks
3. **Parse data consistently** with existing format
4. **Add proper metadata** (source, date, category)
5. **Test thoroughly** with real data

## Documentation Guidelines

- Keep documentation up-to-date
- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Maintain consistent formatting

## Security Considerations

- Never commit secrets or API keys
- Validate all user inputs
- Use secure authentication practices
- Follow OWASP guidelines
- Report security issues privately

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Discord/Slack**: For real-time chat (if available)
- **Email**: For private matters

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation
- Conference presentations (with permission)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

Thank you for contributing to Gaia Mentorship! 🌟
