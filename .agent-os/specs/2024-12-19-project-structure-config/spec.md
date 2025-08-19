# Spec Requirements Document

> Spec: Project Structure and Configuration Management
> Created: 2024-12-19

## Overview

Establish the foundational Python package structure and configuration management system for the Home Assistant Activity Ingestor service. This will provide the base architecture needed for MQTT and WebSocket client implementation.

## User Stories

### Developer Setup Story

As a **developer**, I want a clear, well-structured Python package with proper configuration management, so that I can easily set up the development environment and begin implementing core functionality without confusion about project organization.

**Workflow:** Developer clones the repository, runs `poetry install`, copies `env.example` to `.env`, configures their Home Assistant credentials, and can immediately start the service with `poetry run python -m ha_ingestor.main`.

### Configuration Management Story

As a **DevOps engineer**, I want environment-based configuration with validation, so that I can deploy the service in different environments (development, staging, production) with appropriate settings and clear error messages for missing or invalid configuration.

**Workflow:** DevOps engineer sets environment variables, the service validates all required configuration on startup, provides clear error messages for missing values, and fails fast if critical configuration is invalid.

## Spec Scope

1. **Python Package Structure** - Create the basic `ha_ingestor` package with proper `__init__.py`, `main.py`, and module organization
2. **Configuration Management** - Implement environment variable loading with Pydantic validation and clear error handling
3. **Dependency Management** - Set up Poetry with `pyproject.toml` including all required dependencies for MQTT, WebSocket, and InfluxDB
4. **Basic Logging** - Implement structured logging with configurable levels and JSON formatting
5. **Environment Templates** - Create `.env.example` with all required configuration variables and clear documentation

## Out of Scope

- MQTT client implementation (separate spec)
- WebSocket client implementation (separate spec)
- InfluxDB writer implementation (separate spec)
- Health check endpoints (Phase 2)
- Prometheus metrics (Phase 2)
- Docker containerization (Phase 2)

## Expected Deliverable

1. **Complete Python package structure** that can be imported and run with `python -m ha_ingestor.main`
2. **Configuration system** that loads and validates all required environment variables with clear error messages
3. **Poetry setup** with all dependencies installed and virtual environment working
4. **Basic logging** that outputs structured JSON logs with configurable levels
5. **Environment configuration** that allows developers to quickly set up their local development environment
