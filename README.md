# 🏠 Home Assistant Activity Ingestor

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)
[![Linting](https://img.shields.io/badge/Linting-Ruff-red.svg)](https://github.com/astral-sh/ruff)
[![Type Checking](https://img.shields.io/badge/Type%20Checking-MyPy-blue.svg)](https://mypy-lang.org/)
[![Tests](https://img.shields.io/badge/Tests-Pytest-green.svg)](https://docs.pytest.org/)
[![Pre-commit](https://img.shields.io/badge/Pre--commit-enabled-brightgreen.svg)](https://pre-commit.com/)

A **production-grade Python service** that ingests all relevant Home Assistant activity in real-time and writes it to InfluxDB with advanced filtering, transformation, and monitoring capabilities.

## ✨ Features

### 🚀 **Core Functionality**
- **Real-time ingestion** from Home Assistant MQTT and WebSocket APIs
- **Advanced filtering system** with domain, entity, attribute, and time-based filters
- **Data transformation pipeline** with field mapping and type conversion
- **InfluxDB optimization** with batching, compression, and schema optimization
- **Circuit breaker patterns** and retry logic for reliability

### 📊 **Monitoring & Observability**
- **Comprehensive metrics** collection with Prometheus export
- **Health monitoring** with dependency checking and status endpoints
- **Structured logging** with correlation tracking and context management
- **Performance profiling** and filter execution timing
- **Connection monitoring** with latency and throughput tracking

### 🛡️ **Production Features**
- **Type-safe implementation** with extensive type annotations
- **Pre-commit hooks** for code quality (Black, Ruff, MyPy)
- **Comprehensive testing** framework with pytest
- **Docker support** with docker-compose for easy deployment
- **Environment-based configuration** with Pydantic validation

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+**
- **Home Assistant instance** (confirmed available at `http://192.168.1.86:8123/` ✅)
- **MQTT broker** (typically runs on same network as Home Assistant)
- **InfluxDB instance** for time-series data storage

### 1. Test Connectivity
First, verify your Home Assistant connections work:

```bash
# Install required libraries
pip install websockets paho-mqtt

# Run connectivity test
python test_connectivity.py
```

This will test both WebSocket and MQTT connections to your Home Assistant instance.

### 2. Environment Setup
Copy and configure your environment:

```bash
cp env.example .env
# Edit .env with your MQTT credentials and InfluxDB settings
```

**Note:** Your Home Assistant WebSocket token is already configured! ✅

### 3. Install Dependencies
```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 4. Run the Service
```bash
# Run in development mode
poetry run python -m ha_ingestor.main

# Run with debug logging
LOG_LEVEL=DEBUG poetry run python -m ha_ingestor.main
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Home Assistant│    │   ha-ingestor    │    │    InfluxDB     │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │   MQTT      │◄────┤ │   MQTT       │ │    │ │             │ │
│ │   Broker    │ │    │ │   Client     │ │    │ │             │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ │             │ │
│                 │    │                  │    │ │             │ │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ │             │ │
│ │ WebSocket   │◄────┤ │  WebSocket   │ │    │ │             │ │
│ │   API       │ │    │ │   Client     │ │    │ │             │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ │             │ │
└─────────────────┘    │                  │    │ │             │ │
                       │ ┌──────────────┐ │    │ │             │ │
                       │ │   Filter     │ │    │ │             │ │
                       │ │   Chain      │ │    │ │             │ │
                       │ └──────────────┘ │    │ │             │ │
                       │                  │    │ │             │ │
                       │ ┌──────────────┐ │    │ │             │ │
                       │ │Transformer   │ │    │ │             │ │
                       │ │  Pipeline    │ │    │ │             │ │
                       │ └──────────────┘ │    │ │             │ │
                       │                  │    │ │             │ │
                       │ ┌──────────────┐ │    │ │             │ │
                       │ │ InfluxDB     │◄────┤ │             │ │
                       │ │  Writer      │ │    │ │             │ │
                       │ └──────────────┘ │    │ └─────────────┘ │
                       └──────────────────┘    └─────────────────┘
```

## 📋 What's Ready

✅ **Product Planning Complete** - Full roadmap and technical specifications
✅ **Home Assistant Token** - WebSocket authentication configured
✅ **Environment Configuration** - Template with your HA instance details
✅ **Connectivity Test** - Ready to verify your setup
✅ **Development Guide** - Step-by-step setup instructions
✅ **Code Quality Infrastructure** - Pre-commit hooks, linting, type checking
✅ **Comprehensive Testing** - Unit, integration, and performance tests
✅ **Production Features** - Monitoring, metrics, health checks, error handling

## 🔧 Development

### Code Quality
```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy ha_ingestor/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=ha_ingestor

# Run specific test categories
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m performance
```

### Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# Run tests in Docker
docker-compose run --rm app poetry run pytest
```

## 📚 Documentation

- **`.agent-os/product/`** - Complete product planning documents
- **`.agent-os/specs/`** - Technical specifications and architecture
- **`DEVELOPMENT.md`** - Detailed development setup guide
- **`env.example`** - Environment configuration template
- **`test_connectivity.py`** - Quick connectivity test

## 🎯 Roadmap

### Phase 1: Core Implementation ✅
- [x] Development environment setup
- [x] Code quality infrastructure
- [x] Basic client implementations
- [x] Core data models

### Phase 2: Advanced Features 🔄
- [x] Configurable filtering system
- [x] Data transformation pipeline
- [x] Advanced monitoring and metrics
- [x] Error handling and recovery

### Phase 3: Production Readiness 📋
- [ ] Performance optimization
- [ ] Advanced InfluxDB schema
- [ ] Comprehensive testing
- [ ] Deployment automation

### Phase 4: Advanced Features & Optimization 📋
- [ ] Advanced filtering algorithms
- [ ] Machine learning integration
- [ ] Multi-tenant support
- [ ] Advanced analytics

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Standards
- Follow **PEP 8** with project-specific overrides
- Use **type hints** throughout the codebase
- Write **comprehensive tests** for all new functionality
- Follow **async-first** patterns for I/O operations
- Use **structured logging** with appropriate context

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/wtthornton/ha-ingestor/issues)
- **Documentation**: See `DEVELOPMENT.md` for troubleshooting and detailed setup
- **Roadmap**: Check `.agent-os/product/roadmap.md` for development plans

## 🙏 Acknowledgments

- **Home Assistant** team for the excellent API and ecosystem
- **InfluxData** for the powerful time-series database
- **Python community** for the amazing tools and libraries
- **Context7** for development standards and best practices

---

**Made with ❤️ for the Home Assistant community**
