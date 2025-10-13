# HA Ingestor

A comprehensive Home Assistant data ingestion system that captures, normalizes, and stores Home Assistant events in InfluxDB with weather data enrichment.

[![System Health](https://img.shields.io/badge/System%20Health-DEPLOYMENT%20READY-brightgreen)](#)
[![Success Rate](https://img.shields.io/badge/Success%20Rate-75%25-green)](#)
[![Critical Issues](https://img.shields.io/badge/Critical%20Issues-0-brightgreen)](#)
[![Production Ready](https://img.shields.io/badge/Production-Ready-brightgreen)](#)

## 🎯 **Recent Updates (October 2025)**

✅ **Data Enrichment Platform Complete** - 5 new external data services fully integrated  
✅ **Advanced Storage Optimization** - Tiered retention, materialized views, and S3 archival  
✅ **Multi-Source Data Integration** - Carbon intensity, electricity pricing, air quality, calendar, and smart meter data  
✅ **Storage Analytics** - Comprehensive monitoring and optimization of time-series data  
✅ **All Critical Issues Resolved** - System upgraded to DEPLOYMENT READY status  
✅ **WebSocket Connection Fixed** - Enhanced logging, authentication timing, and subscription management  
✅ **Dashboard 502 Error Resolved** - Fixed nginx proxy configuration for API calls  
✅ **Dashboard Enhanced** - Database Storage, Error Rate, and Weather API monitoring with detailed metrics  

## ⚠️ **Important: Docker Configuration**

**Before making ANY changes to Dockerfiles or nginx configs, read:**
- 📘 **[Docker Structure Guide](docs/DOCKER_STRUCTURE_GUIDE.md)** - Complete guide to Docker structure (DO NOT BREAK THIS!)
- 🚀 **[Quick Reference](docs/QUICK_REFERENCE_DOCKER.md)** - Quick reference for common tasks

**Critical files that must not be broken:**
- `services/websocket-ingestion/Dockerfile` - Uses `python -m src.main`
- `services/admin-api/Dockerfile` - Requires `ENV PYTHONPATH=/app:/app/src`
- `services/health-dashboard/nginx.conf` - API proxy configuration

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Home Assistant instance with long-lived access token
- OpenWeatherMap API key (optional, for weather data)

### 🔑 Authentication Setup

**Important:** The `.env` file contains all required tokens and API keys. Before deployment, ensure you have:

#### Home Assistant Token
1. **Access Home Assistant**: Open your Home Assistant instance in a browser
2. **Generate Token**: Go to Profile → Long-Lived Access Tokens → Create Token
3. **Name it**: Give it a descriptive name (e.g., "HA Ingestor")
4. **Copy Token**: Save the generated token immediately (it won't be shown again)
5. **Update .env**: Set `HOME_ASSISTANT_TOKEN=your_token_here`

#### Required Environment Variables
The `.env` file should contain:
```bash
# Home Assistant Configuration
HOME_ASSISTANT_URL=http://your-ha-ip:8123
HOME_ASSISTANT_TOKEN=your_long_lived_access_token

# Optional: Weather API (for data enrichment)
WEATHER_API_KEY=your_openweathermap_api_key
WEATHER_DEFAULT_LOCATION=Your City,State,Country

# Database Configuration
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_BUCKET=home_assistant_events
```

#### Token Validation
Before deployment, validate your tokens:
```bash
# Test Home Assistant connection
python tests/test_local_ha_connection.py

# Test all API keys
python tests/test_api_keys.py

# Full system integration test
python tests/test_system_integration.py
```

**Common Issues:**
- **401 Unauthorized**: Token is invalid or expired - generate a new one
- **Connection Failed**: Check Home Assistant URL and network connectivity
- **Permission Denied**: Ensure token has proper permissions for WebSocket access

### Setup

#### 🚀 Quick Start with Deployment Wizard (Recommended)

The easiest way to get started:

```bash
# 1. Clone the repository
git clone <repository-url>
cd ha-ingestor

# 2. Run the deployment wizard
./scripts/deploy-wizard.sh

# 3. Start services
docker-compose up -d

# 4. Access dashboard
open http://localhost:3000
```

The deployment wizard will:
- ✅ Guide you through deployment options
- ✅ Configure Home Assistant connection
- ✅ Auto-detect system resources
- ✅ Generate secure configuration
- ✅ Validate connectivity

**See:** [`docs/DEPLOYMENT_WIZARD_GUIDE.md`](docs/DEPLOYMENT_WIZARD_GUIDE.md) for detailed usage.

---

#### Alternative Setup Methods

**1. Interactive Environment Setup:**
   
   **Linux/Mac:**
   ```bash
   ./scripts/setup-secure-env.sh
   ```
   
   **Windows:**
   ```powershell
   .\scripts\setup-secure-env.ps1
   ```

**2. Manual Setup:**
   ```bash
   cp infrastructure/env.example .env
   # Edit .env with your values
   ```

**3. Validate Configuration:**
   ```bash
   # Test your connection before deployment
   ./scripts/validate-ha-connection.sh
   ```

---

#### Development Environment

For development work:

```bash
# Start development environment
./scripts/start-dev.sh

# Test services
./scripts/test-services.sh
```

### 🔒 Security Note

This project follows security best practices:
- ✅ Sensitive files (env.production, .env) are in `.gitignore`
- ✅ No secrets are committed to the repository
- ✅ Secure setup scripts generate random passwords
- ✅ GitHub Actions workflow supports secret management

**Important:** Never commit files containing actual API keys or passwords!

📖 See [Security Configuration Guide](docs/SECURITY_CONFIGURATION.md) for details.

## Services

### Core Services

#### WebSocket Ingestion Service
- Connects to Home Assistant WebSocket API
- Subscribes to state_changed events
- Handles authentication and reconnection
- Enhanced logging with correlation IDs
- Weather enrichment integration
- Port: 8001 (external)

#### Enrichment Pipeline Service
- Processes and enriches Home Assistant events
- Data validation and quality metrics
- Normalization and InfluxDB storage
- Multi-source enrichment coordination
- Quality dashboard and alerting
- Port: 8002 (external)

#### Data Retention Service (Enhanced)
- Manages data lifecycle and cleanup
- Tiered storage (hot/warm/cold)
- Materialized views for fast queries
- S3/Glacier archival support
- Storage analytics and optimization
- Backup and restore operations
- Port: 8080 (external)

#### Admin API Service
- Provides REST API gateway for all services
- Centralized health monitoring
- **Docker service control** (start/stop/restart containers)
- **Integration management UI** (HA, Weather, InfluxDB config)
- System-wide metrics and statistics
- WebSocket endpoints for real-time updates
- Devices & entities registry
- Alert management system
- Port: 8003 (mapped to container 8004)

#### Health Dashboard
- **12 comprehensive tabs** (Overview, Custom, Services, Dependencies, Devices, Events, Logs, Sports, Data Sources, Analytics, Alerts, Configuration)
- **Interactive dependency graph** with click-to-highlight visualization
- Real-time WebSocket integration
- **Customizable widget dashboard** (drag & drop)
- Mobile-responsive design with dark mode
- Configuration management UI (no terminal needed)
- Port: 3000 (external)

### External Data Services

#### Sports Data Service
- **NFL & NHL game tracking** using **FREE ESPN API**
- Team-based filtering (user selects favorite teams)
- Live game status and upcoming games
- Smart caching (15s for live, 5min for upcoming)
- Full dashboard integration with Setup Wizard
- Port: 8005 (external)
- **Status:** ✅ Production Ready

#### Carbon Intensity Service
- Fetches carbon intensity data from National Grid
- Regional carbon metrics
- Renewable energy percentage
- Port: 8010 (internal)

#### Electricity Pricing Service
- Real-time electricity pricing data
- Support for multiple providers (Octopus Energy, etc.)
- Time-of-use tariff information
- Port: 8011 (internal)

#### Air Quality Service
- Air quality index and pollutant levels
- Data from OpenAQ and government sources
- Health recommendations
- Port: 8012 (internal)

#### Calendar Service
- Integrates with Google Calendar, Outlook, iCal
- Event-based automation triggers
- Holiday and schedule tracking
- Port: 8013 (internal)

#### Smart Meter Service
- Smart meter data integration
- Support for multiple protocols (SMETS2, P1, etc.)
- Real-time energy consumption
- Port: 8014 (internal)

### Data Storage & Monitoring

#### Weather API Service
- Fetches weather data from OpenWeatherMap
- Enriches Home Assistant data with weather context
- Integrated into websocket-ingestion service
- Port: Internal (no external access)

#### Log Aggregator Service
- Centralized log collection from all Docker containers
- JSON log aggregation and analysis
- Port: 8015 (external)

#### InfluxDB
- Time-series database for event storage
- Tiered storage with downsampling
- Web interface for data exploration
- Port: 8086

## Development

### Project Structure

```
ha-ingestor/
├── services/                      # 12 microservices (Alpine-based)
│   ├── websocket-ingestion/      # Port 8001 - HA WebSocket client
│   ├── enrichment-pipeline/      # Port 8002 - Data processing
│   ├── admin-api/                # Port 8003 - REST API gateway
│   ├── data-retention/           # Port 8080 - Data lifecycle
│   ├── health-dashboard/         # Port 3000 - React UI (12 tabs)
│   ├── sports-data/              # Port 8005 - ESPN API integration
│   ├── log-aggregator/           # Port 8015 - Log aggregation
│   ├── weather-api/              # Internal - Weather enrichment
│   ├── carbon-intensity-service/ # Port 8010 - Carbon data
│   ├── electricity-pricing-service/ # Port 8011 - Pricing
│   ├── air-quality-service/      # Port 8012 - Air quality
│   ├── calendar-service/         # Port 8013 - Calendar
│   ├── smart-meter-service/      # Port 8014 - Smart meter
│   └── ha-simulator/             # Test simulator for HA events
├── shared/                       # Shared Python utilities
│   ├── logging_config.py         # Structured logging + correlation IDs
│   ├── correlation_middleware.py # Request tracking
│   ├── metrics_collector.py      # Metrics framework
│   └── alert_manager.py          # Alert management
├── infrastructure/               # Environment configs
│   ├── .env.websocket            # WebSocket config
│   ├── .env.weather              # Weather API config
│   └── .env.influxdb             # InfluxDB config
├── scripts/                      # Deployment scripts
├── tests/                        # Integration & E2E tests (Playwright)
├── tools/cli/                    # CLI utilities
└── docs/                         # Comprehensive documentation
```

### Available Scripts

**Environment Setup:**
- `./scripts/setup-secure-env.sh` - Interactive secure environment setup (Linux/Mac)
- `./scripts/setup-secure-env.ps1` - Interactive secure environment setup (Windows)
- `./scripts/setup-env.sh` - Simple environment setup (legacy)

**Configuration Management:**
- `./scripts/setup-config.sh` - Interactive service configuration setup (Linux/Mac)
- `./scripts/setup-config.ps1` - Interactive service configuration setup (Windows)

**Development:**
- `./scripts/start-dev.sh` - Start development environment
- `./scripts/start-prod.sh` - Start production environment
- `./scripts/test-services.sh` - Test all services
- `./scripts/view-logs.sh` - View service logs
- `./scripts/cleanup.sh` - Clean up Docker resources

### Docker Compose Files

- `docker-compose.yml` - Main configuration
- `docker-compose.dev.yml` - Development environment
- `docker-compose.prod.yml` - Production environment

## Configuration Management

### Web-Based Configuration (Recommended)

The Health Dashboard provides a user-friendly interface for managing service configurations:

1. **Access Dashboard**: Navigate to `http://localhost:3000`
2. **Open Configuration**: Click the 🔧 **Configuration** tab
3. **Select Service**: Click on a service card (Home Assistant, Weather API, or InfluxDB)
4. **Edit Settings**: Update API keys, URLs, and other configuration values
5. **Save Changes**: Click "Save Changes" to persist to configuration files
6. **Restart Service**: Restart the service via command line for changes to take effect

**Supported Services:**
- **Home Assistant WebSocket** - Connection URL and access token
- **Weather API** - OpenWeatherMap API key and location settings
- **InfluxDB** - Database connection and credentials

**Security Features:**
- API keys and tokens are masked (••••••••) by default
- Show/Hide toggle for sensitive values
- Configuration files are automatically set to secure permissions (600)

### Command-Line Configuration

For automated or scripted setup:

**Linux/Mac:**
```bash
./scripts/setup-config.sh
```

**Windows:**
```powershell
.\scripts\setup-config.ps1
```

These scripts provide interactive prompts to configure all services.

📖 **See:** [Configuration Management Guide](docs/QUICK_START_INTEGRATION_MANAGEMENT.md)

## Health Checks

All services expose health check endpoints:

### Core Services
- Admin API: `http://localhost:8003/health`
- Admin API Full Docs: `http://localhost:8003/docs` (when auth disabled)
- Admin API Configuration: `http://localhost:8003/api/v1/integrations`
- WebSocket Ingestion: `http://localhost:8001/health`
- Enrichment Pipeline: `http://localhost:8002/health`
- Data Retention: `http://localhost:8080/health`
- Sports Data: `http://localhost:8005/health`
- Log Aggregator: `http://localhost:8015/health`
- Health Dashboard: `http://localhost:3000`
- InfluxDB: `http://localhost:8086/health`

### External Data Services (Internal Network Only)
- Carbon Intensity: Internal health checks only
- Electricity Pricing: Internal health checks only
- Air Quality: Internal health checks only
- Calendar: Internal health checks only
- Smart Meter: Internal health checks only
- Weather API: Internal health checks only

## Monitoring

### Logs
View logs for all services:
```bash
./scripts/view-logs.sh
```

### Service Status
Test all services:
```bash
./scripts/test-services.sh
```

## Production Deployment

### Option 1: Manual Deployment (Recommended for Self-Hosted)

1. **Configure production environment securely:**
   ```bash
   ./scripts/setup-secure-env.sh
   # Select "Production" when prompted
   ```

2. **Start production environment:**
   ```bash
   ./scripts/start-prod.sh
   ```

3. **Monitor services:**
   ```bash
   ./scripts/test-services.sh
   ```

### Option 2: CI/CD with GitHub Actions

1. **Add secrets to GitHub:**
   - Go to: `Settings` → `Secrets and variables` → `Actions`
   - Add required secrets (see [GitHub Secrets Guide](docs/GITHUB_SECRETS_SETUP.md))

2. **Enable workflow:**
   ```bash
   mv .github/workflows/deploy-production.yml.example .github/workflows/deploy-production.yml
   ```

3. **Push to trigger deployment:**
   ```bash
   git push origin main
   ```

📖 **Detailed Guides:**
- [Security Configuration Guide](docs/SECURITY_CONFIGURATION.md) - Complete security setup
- [GitHub Secrets Setup](docs/GITHUB_SECRETS_SETUP.md) - CI/CD deployment guide
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Full deployment documentation

## Troubleshooting

### Common Issues

1. **Services not starting:**
   - Check environment variables in `.env`
   - Verify Docker is running
   - Check logs: `./scripts/view-logs.sh`

2. **Home Assistant connection issues:**
   - Verify `HOME_ASSISTANT_URL` and `HOME_ASSISTANT_TOKEN` in `.env`
   - Check Home Assistant is accessible: `curl http://your-ha-ip:8123`
   - Test token validity: `python tests/test_local_ha_connection.py`
   - Ensure token has proper permissions for WebSocket access
   - **401 Unauthorized**: Generate a new Long-Lived Access Token
   - **Connection Failed**: Check network connectivity and firewall settings

3. **WebSocket connection issues:**
   - Check WebSocket service logs: `docker-compose logs websocket-ingestion`
   - Verify authentication timing (1-second delay added for stability)
   - Check subscription status in health endpoint
   - See [WebSocket Troubleshooting Guide](docs/WEBSOCKET_TROUBLESHOOTING.md)

4. **Dashboard 502 errors:**
   - Check nginx proxy configuration in `services/health-dashboard/nginx.conf`
   - Verify admin-api service is running: `docker-compose ps admin-api`
   - Test API endpoints directly: `curl http://localhost:8003/api/v1/health`

5. **InfluxDB connection issues:**
   - Check InfluxDB credentials
   - Verify network connectivity
   - Check InfluxDB logs

### Cleanup

Clean up all Docker resources:
```bash
./scripts/cleanup.sh
```

## Contributing

1. Follow the coding standards in `docs/architecture/coding-standards.md`
2. Use the development environment for testing
3. Run tests before submitting changes
4. Update documentation as needed

## License

MIT License

Copyright (c) 2025 Home Assistant Ingestor Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
