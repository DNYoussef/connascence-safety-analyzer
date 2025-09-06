# Makefile for Release Management
# Connascence Analyzer Release Automation

.PHONY: help validate bump-major bump-minor bump-patch release-notes build test clean
.DEFAULT_GOAL := help

# Configuration
PYTHON := python
VERSION_SCRIPT := scripts/release/bump_version.py
NOTES_SCRIPT := scripts/release/generate_release_notes.py
VALIDATE_SCRIPT := scripts/release/validate_release.py

help: ## Show this help message
	@echo "Connascence Analyzer Release Management"
	@echo "======================================"
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

validate: ## Run pre-release validation checks
	@echo "Running pre-release validation..."
	$(PYTHON) $(VALIDATE_SCRIPT) --verbose

bump-major: validate ## Bump major version (X.0.0)
	@echo "Bumping major version..."
	$(PYTHON) $(VERSION_SCRIPT) major

bump-minor: validate ## Bump minor version (X.Y.0)
	@echo "Bumping minor version..."
	$(PYTHON) $(VERSION_SCRIPT) minor

bump-patch: validate ## Bump patch version (X.Y.Z)
	@echo "Bumping patch version..."
	$(PYTHON) $(VERSION_SCRIPT) patch

bump-major-dry: ## Preview major version bump
	$(PYTHON) $(VERSION_SCRIPT) major --dry-run

bump-minor-dry: ## Preview minor version bump
	$(PYTHON) $(VERSION_SCRIPT) minor --dry-run

bump-patch-dry: ## Preview patch version bump
	$(PYTHON) $(VERSION_SCRIPT) patch --dry-run

release-notes: ## Generate release notes for current version
	@VERSION=$$($(PYTHON) -c "import tomllib; f=open('pyproject.toml','rb'); print(tomllib.load(f)['project']['version'])"); \
	echo "Generating release notes for version $$VERSION..."; \
	$(PYTHON) $(NOTES_SCRIPT) $$VERSION --output docs/release-notes/$$VERSION.md

build: clean ## Build distribution packages
	@echo "Building distribution packages..."
	$(PYTHON) -m build

test: ## Run test suite with coverage
	@echo "Running test suite..."
	$(PYTHON) -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html

lint: ## Run code quality checks
	@echo "Running code quality checks..."
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy . --ignore-missing-imports

security: ## Run security analysis
	@echo "Running security analysis..."
	$(PYTHON) -m connascence . --policy=nasa_jpl_pot10 --format=json

clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f coverage.json
	rm -f .coverage

install-dev: ## Install development dependencies
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"

# Full release workflow targets

prepare-release: validate lint test security ## Run all pre-release checks
	@echo "All pre-release checks completed successfully!"

create-release: ## Create and tag a release (requires VERSION env var)
ifndef VERSION
	@echo "Error: VERSION environment variable is required"
	@echo "Usage: make create-release VERSION=1.0.1"
	@exit 1
endif
	@echo "Creating release $(VERSION)..."
	git add .
	git commit -m "Bump version to $(VERSION)"
	git tag v$(VERSION)
	git push origin main
	git push origin v$(VERSION)
	@echo "Release $(VERSION) created successfully!"

publish: build ## Publish to PyPI (requires built packages)
	@echo "Publishing to PyPI..."
	$(PYTHON) -m twine upload dist/*

publish-test: build ## Publish to TestPyPI
	@echo "Publishing to TestPyPI..."
	$(PYTHON) -m twine upload --repository testpypi dist/*

# Complete release workflow
full-release: prepare-release ## Complete release workflow (interactive)
	@echo "Starting full release workflow..."
	@echo "1. Running validation..."
	@make validate
	@echo ""
	@echo "2. Choose release type:"
	@echo "   - major: Breaking changes (X.0.0)"
	@echo "   - minor: New features (X.Y.0)"  
	@echo "   - patch: Bug fixes (X.Y.Z)"
	@read -p "Release type [patch]: " release_type; \
	release_type=$${release_type:-patch}; \
	echo "Creating $$release_type release..."; \
	$(PYTHON) $(VERSION_SCRIPT) $$release_type
	@VERSION=$$($(PYTHON) -c "import tomllib; f=open('pyproject.toml','rb'); print(tomllib.load(f)['project']['version'])"); \
	echo ""; \
	echo "3. Generating release notes for $$VERSION..."; \
	$(PYTHON) $(NOTES_SCRIPT) $$VERSION --output docs/release-notes/$$VERSION.md; \
	echo ""; \
	echo "4. Please review and update:"; \
	echo "   - CHANGELOG.md (move items from Unreleased)"; \
	echo "   - docs/release-notes/$$VERSION.md (review generated notes)"; \
	echo ""; \
	echo "5. When ready, run: make create-release VERSION=$$VERSION"; \
	echo "6. Then run: make publish"

# Development helpers
check: lint test security ## Run all quality checks

watch-tests: ## Run tests in watch mode (requires pytest-watch)
	ptw --runner "python -m pytest tests/ --cov=. --cov-report=term-missing"

docs-serve: ## Serve documentation locally
	@echo "Serving documentation at http://localhost:8000"
	@cd docs && $(PYTHON) -m http.server 8000

# GitHub CLI helpers (requires gh command)
gh-release: ## Create GitHub release (requires VERSION env var)
ifndef VERSION
	@echo "Error: VERSION environment variable is required"
	@exit 1
endif
	@echo "Creating GitHub release for $(VERSION)..."
	gh release create v$(VERSION) --title "Connascence Analyzer $(VERSION)" --notes-file docs/release-notes/$(VERSION).md

gh-draft: ## Create draft GitHub release (requires VERSION env var)  
ifndef VERSION
	@echo "Error: VERSION environment variable is required"
	@exit 1
endif
	@echo "Creating draft GitHub release for $(VERSION)..."
	gh release create v$(VERSION) --draft --title "Connascence Analyzer $(VERSION)" --notes-file docs/release-notes/$(VERSION).md