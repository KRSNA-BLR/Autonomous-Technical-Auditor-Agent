# =============================================================================
# Makefile - Development Automation Commands
# =============================================================================
# This Makefile provides convenient commands for development, testing,
# and deployment of the Autonomous Tech Research Agent.
#
# Usage: make <target>
# Example: make install
# =============================================================================

.PHONY: help install install-dev lint format typecheck test test-cov run run-dev docker-build docker-run clean

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python
PIP := pip
UVICORN := uvicorn
PYTEST := pytest
RUFF := ruff
MYPY := mypy

# Colors for terminal output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo ""
	@echo "$(BLUE)Autonomous Tech Research Agent$(NC)"
	@echo "$(YELLOW)================================$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

# =============================================================================
# Installation
# =============================================================================

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(PIP) install -e .
	@echo "$(GREEN)✓ Installation complete$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)✓ Development installation complete$(NC)"

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linting with ruff
	@echo "$(BLUE)Running ruff linter...$(NC)"
	$(RUFF) check src/ tests/
	@echo "$(GREEN)✓ Linting complete$(NC)"

lint-fix: ## Run linting and auto-fix issues
	@echo "$(BLUE)Running ruff with auto-fix...$(NC)"
	$(RUFF) check src/ tests/ --fix
	@echo "$(GREEN)✓ Linting and fixes complete$(NC)"

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	$(RUFF) format src/ tests/
	@echo "$(GREEN)✓ Formatting complete$(NC)"

typecheck: ## Run static type checking with mypy
	@echo "$(BLUE)Running mypy type checker...$(NC)"
	$(MYPY) src/
	@echo "$(GREEN)✓ Type checking complete$(NC)"

quality: lint typecheck ## Run all code quality checks
	@echo "$(GREEN)✓ All quality checks passed$(NC)"

# =============================================================================
# Testing
# =============================================================================

test: ## Run tests with pytest
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTEST) tests/ -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

test-unit: ## Run only unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTEST) tests/unit/ -v -m unit
	@echo "$(GREEN)✓ Unit tests complete$(NC)"

test-integration: ## Run only integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(PYTEST) tests/integration/ -v -m integration
	@echo "$(GREEN)✓ Integration tests complete$(NC)"

# =============================================================================
# Running the Application
# =============================================================================

run: ## Run the application in production mode
	@echo "$(BLUE)Starting application...$(NC)"
	$(UVICORN) src.infrastructure.api.main:app --host 0.0.0.0 --port 8000
	
run-dev: ## Run the application in development mode with auto-reload
	@echo "$(BLUE)Starting application in development mode...$(NC)"
	$(UVICORN) src.infrastructure.api.main:app --host 0.0.0.0 --port 8000 --reload

# =============================================================================
# Docker
# =============================================================================

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t research-agent:latest .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -p 8000:8000 --env-file .env research-agent:latest

docker-up: ## Start services with docker-compose
	@echo "$(BLUE)Starting services with docker-compose...$(NC)"
	docker-compose up --build

docker-down: ## Stop docker-compose services
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose down

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean up generated files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage coverage.xml
	rm -rf dist build *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# =============================================================================
# Development Workflow
# =============================================================================

setup: install-dev ## Complete development setup
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Copy .env.example to .env and add your GROQ_API_KEY"
	@echo "  2. Run 'make run-dev' to start the development server"
	@echo "  3. Visit http://localhost:8000/docs for API documentation"

check: format lint typecheck test ## Run all checks before committing
	@echo "$(GREEN)✓ All checks passed! Ready to commit.$(NC)"
