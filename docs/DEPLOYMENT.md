# HA Ingestor Production Deployment Guide

This guide provides comprehensive instructions for deploying the HA Ingestor system in a production environment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment Methods](#deployment-methods)
- [Environment Setup](#environment-setup)
- [Service Management](#service-management)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Security Considerations](#security-considerations)

## Prerequisites

### Required Software

- **Docker**: Version 20.10+ 
- **Docker Compose**: Version 2.0+
- **Git**: For cloning the repository
- **Python**: Version 3.8+ (for testing and CLI tools)

### Required Accounts

- **Home Assistant**: Long-lived access token
- **OpenWeatherMap**: API key for weather data enrichment

## System Requirements

### Minimum Requirements

- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 20GB available space
- **Network**: Stable internet connection

### Recommended Requirements

- **CPU**: 4+ cores for high-volume processing
- **Memory**: 8GB+ RAM for optimal performance
- **Storage**: 50GB+ SSD storage for database performance
- **Network**: Gigabit ethernet for Home Assistant connectivity

### Hardware Compatibility

The system has been tested on:
- Intel x64 processors
- ARM64 processors (Raspberry Pi 4+)
- Virtual machines (VMware, VirtualBox)
- Docker Desktop on Windows/Mac
- Linux containers

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd homeiq
```

### 2. Configure Environment

```bash
# Copy the production environment template
cp infrastructure/env.production .env.production

# Edit with your actual values
nano .env.production
```

### 3. Deploy with Docker Compose

#### Linux/macOS:
```bash
./scripts/deploy.sh
```

#### Windows:
```powershell
.\scripts\deploy.ps1
```

### 4. Verify Deployment

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Access health dashboard
open http://localhost:3000
```

## Configuration

### Environment Variables

The production deployment uses `infrastructure/env.production` for configuration. Key variables include:

#### Home Assistant Configuration
```bash
HOME_ASSISTANT_URL=http://your-ha-instance:8123
HOME_ASSISTANT_TOKEN=your_long_lived_access_token_here
```

#### InfluxDB Configuration
```bash
INFLUXDB_USERNAME=admin
INFLUXDB_PASSWORD=your_secure_password_here
INFLUXDB_ORG=homeiq
INFLUXDB_BUCKET=home_assistant_events
INFLUXDB_TOKEN=your_secure_token_here
```

#### Weather API Configuration
```bash
WEATHER_API_KEY=your_openweathermap_api_key_here
WEATHER_API_URL=https://api.openweathermap.org/data/2.5
ENABLE_WEATHER_API=true
```

#### Security Configuration
```bash
ENABLE_AUTH=true
JWT_SECRET_KEY=your_secure_jwt_secret_key_here
ADMIN_PASSWORD=your_secure_admin_password_here
```

### Service Configuration

#### Resource Limits
Each service has configured resource limits:

- **InfluxDB**: 2GB memory, 2 CPU cores
- **WebSocket Ingestion**: 512MB memory, 0.5 CPU cores
- **Enrichment Pipeline**: 1GB memory, 1 CPU core
- **Admin API**: 512MB memory, 0.5 CPU cores
- **Data Retention**: 1GB memory, 1 CPU core
- **Health Dashboard**: 256MB memory, 0.25 CPU cores

#### Network Configuration
- **Network**: `homeiq-network` (172.20.0.0/16)
- **Service Discovery**: Internal DNS resolution
- **Port Mapping**: Only necessary ports exposed

## Deployment Methods

### Method 1: Automated Deployment Script

The recommended approach using the deployment script:

```bash
# Full deployment
./scripts/deploy.sh

# Validate configuration only
./scripts/deploy.sh validate

# Show status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs
```

### Method 2: Manual Docker Compose

For advanced users who prefer manual control:

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml --env-file infrastructure/env.production up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Method 3: Development Mode

For testing and development:

```bash
# Use development configuration
docker-compose -f docker-compose.dev.yml up -d
```

## Environment Setup

### Production Environment

1. **Create production environment file**:
   ```bash
   cp infrastructure/env.production .env.production
   ```

2. **Configure all required variables**:
   - Home Assistant URL and token
   - InfluxDB credentials
   - Weather API key
   - Security keys and passwords

3. **Validate configuration**:
   ```bash
   ./scripts/deploy.sh validate
   ```

### Development Environment

1. **Create development environment file**:
   ```bash
   cp infrastructure/env.example .env.development
   ```

2. **Configure with development values**:
   - Use development Home Assistant instance
   - Use test API keys
   - Enable debug logging

## Service Management

### Starting Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Start specific service
docker-compose -f docker-compose.prod.yml up -d influxdb
```

### Stopping Services

```bash
# Stop all services gracefully
docker-compose -f docker-compose.prod.yml down

# Stop with timeout
docker-compose -f docker-compose.prod.yml down --timeout 30
```

### Restarting Services

```bash
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart websocket-ingestion
```

### Updating Services

```bash
# Pull latest images and rebuild
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring and Health Checks

### Health Check Endpoints

Each service provides health check endpoints:

- **InfluxDB**: `http://localhost:8086/health`
- **WebSocket Ingestion**: `http://localhost:8001/health`
- **Enrichment Pipeline**: `http://localhost:8002/health`
- **Admin API**: `http://localhost:8003/api/v1/health`
- **Data Retention**: `http://localhost:8080/health`
- **Health Dashboard**: `http://localhost:3000`

### Health Dashboard

Access the comprehensive health dashboard at:
```
http://localhost:3000
```

The dashboard provides:
- Service status overview
- Real-time metrics
- Historical data visualization
- System performance monitoring

### Log Monitoring

#### View All Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

#### View Specific Service Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f websocket-ingestion
```

#### Log Files
Logs are stored in:
- Container logs: `docker logs <container-name>`
- Volume logs: `/var/log/docker/containers/`
- Application logs: `logs/` directory

### Metrics Collection

The system collects various metrics:
- Event processing rates
- API response times
- Database performance
- Resource utilization
- Error rates

Access metrics via:
- Health dashboard: `http://localhost:3000/metrics`
- Admin API: `http://localhost:8003/api/v1/stats`

## Troubleshooting

### Common Issues

#### Services Not Starting

**Problem**: Services fail to start or show unhealthy status

**Solutions**:
1. Check configuration:
   ```bash
   ./scripts/deploy.sh validate
   ```

2. Check logs:
   ```bash
   docker-compose -f docker-compose.prod.yml logs
   ```

3. Verify prerequisites:
   ```bash
   docker --version
   docker-compose --version
   ```

#### Home Assistant Connection Issues

**Problem**: WebSocket ingestion cannot connect to Home Assistant

**Solutions**:
1. Verify Home Assistant URL and token
2. Check network connectivity:
   ```bash
   curl -f http://your-ha-instance:8123/api/
   ```
3. Ensure long-lived access token is valid

#### Database Connection Issues

**Problem**: Services cannot connect to InfluxDB

**Solutions**:
1. Check InfluxDB status:
   ```bash
   docker-compose -f docker-compose.prod.yml ps influxdb
   ```
2. Verify credentials in environment file
3. Check InfluxDB logs:
   ```bash
   docker-compose -f docker-compose.prod.yml logs influxdb
   ```

#### High Memory Usage

**Problem**: Services consuming excessive memory

**Solutions**:
1. Check resource limits in docker-compose.prod.yml
2. Monitor memory usage:
   ```bash
   docker stats
   ```
3. Adjust resource limits if necessary

### Diagnostic Commands

#### System Information
```bash
# Docker system info
docker system info

# Container resource usage
docker stats

# Disk usage
docker system df
```

#### Service Diagnostics
```bash
# Service status
docker-compose -f docker-compose.prod.yml ps

# Service logs
docker-compose -f docker-compose.prod.yml logs

# Health check status
docker inspect $(docker-compose -f docker-compose.prod.yml ps -q) --format='{{.State.Health.Status}}'
```

#### Network Diagnostics
```bash
# Network connectivity
docker network ls
docker network inspect homeiq-network

# Port availability
netstat -tulpn | grep :8086
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor service health and logs
- Check disk space usage
- Verify data ingestion rates

#### Weekly
- Review error logs and metrics
- Check backup status
- Update service dependencies

#### Monthly
- Review and rotate logs
- Analyze performance metrics
- Update security patches

### Backup Procedures

#### Automated Backups
The data retention service handles automated backups:

```bash
# Check backup status
curl http://localhost:8080/api/v1/backup/status

# Manual backup trigger
curl -X POST http://localhost:8080/api/v1/backup/trigger
```

#### Manual Backups
```bash
# Backup InfluxDB data
docker exec homeiq-influxdb influx backup /backup/$(date +%Y%m%d_%H%M%S)

# Backup configuration
cp infrastructure/env.production backups/env.production.$(date +%Y%m%d)
```

### Update Procedures

#### Service Updates
```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Backup current state
./scripts/backup.sh

# Deploy updates
./scripts/deploy.sh

# Verify deployment
./scripts/deploy.sh status
```

#### Configuration Updates
```bash
# Edit configuration
nano infrastructure/env.production

# Validate configuration
./scripts/deploy.sh validate

# Apply changes
docker-compose -f docker-compose.prod.yml up -d
```

### Log Management

#### Log Rotation
Logs are automatically rotated with the following limits:
- Maximum file size: 10MB
- Maximum files: 3 per service
- Retention: 30 days

#### Log Cleanup
```bash
# Clean old logs
docker system prune -f

# Clean specific service logs
docker-compose -f docker-compose.prod.yml logs --tail=0 --follow=false
```

## Security Considerations

### Network Security

- **Internal Communication**: All services communicate over internal Docker network
- **External Access**: Only necessary ports exposed (8086, 8001, 8002, 8003, 8080, 3000)
- **Firewall**: Configure firewall to restrict external access

### Authentication and Authorization

- **API Authentication**: JWT-based authentication for admin API
- **Token Security**: Use strong, unique tokens for all services
- **Password Security**: Strong passwords for all accounts

### Data Security

- **Encryption**: Enable TLS for external communications
- **Backup Encryption**: Encrypt sensitive backup data
- **Access Control**: Limit access to configuration files

### Container Security

- **Non-root Users**: All containers run as non-root users
- **Read-only Filesystems**: Where possible, containers use read-only filesystems
- **Security Options**: Containers use security options to prevent privilege escalation

### Security Best Practices

1. **Regular Updates**: Keep Docker and services updated
2. **Monitor Access**: Monitor access logs and failed authentication attempts
3. **Backup Security**: Secure backup storage and access
4. **Network Segmentation**: Use network segmentation for additional security
5. **Audit Logging**: Enable comprehensive audit logging

## Support and Resources

### Documentation
- [Architecture Documentation](architecture/)
- [API Documentation](api/)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

### Community
- [GitHub Issues](https://github.com/your-org/homeiq/issues)
- [Discord Community](https://discord.gg/your-community)

### Professional Support
For enterprise support and consulting services, contact: support@your-org.com

---

**Last Updated**: 2024-12-19  
**Version**: 1.0.0
