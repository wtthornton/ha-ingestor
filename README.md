# Home Assistant Activity Ingestor

A production-grade Python service that ingests all relevant Home Assistant activity in real-time and writes it to InfluxDB.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Home Assistant instance: **http://192.168.1.86:8123/** ✅ (Confirmed available)
- MQTT broker (typically runs on same network as Home Assistant)
- InfluxDB instance for testing

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

## 📋 What's Ready

✅ **Product Planning Complete** - Full roadmap and technical specifications  
✅ **Home Assistant Token** - WebSocket authentication configured  
✅ **Environment Configuration** - Template with your HA instance details  
✅ **Connectivity Test** - Ready to verify your setup  
✅ **Development Guide** - Step-by-step setup instructions  

## 🎯 Next Steps

1. **Test connectivity** with `python test_connectivity.py`
2. **Configure MQTT credentials** in your `.env` file
3. **Set up InfluxDB** for testing
4. **Start Phase 1 development** following the roadmap

## 📚 Documentation

- **`.agent-os/product/`** - Complete product planning documents
- **`DEVELOPMENT.md`** - Detailed development setup guide
- **`env.example`** - Environment configuration template
- **`test_connectivity.py`** - Quick connectivity test

## 🏗️ Architecture

The service connects to:
- **Home Assistant MQTT Broker** (Mosquitto) for device state changes
- **Home Assistant WebSocket API** for core event-bus activity
- **InfluxDB** for optimized time-series storage

## 🔧 Development

```bash
# Run tests
poetry run pytest

# Code quality
poetry run ruff format .
poetry run ruff check .
poetry run mypy ha_ingestor/
```

## 📞 Support

See `DEVELOPMENT.md` for troubleshooting and detailed setup instructions.
