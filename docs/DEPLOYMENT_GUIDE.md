# 🚀 Home Assistant Ingestor - Deployment Guide

## 📋 **Quick Start**

### **Prerequisites**
- Docker 20.10+ and Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)
- 20GB storage minimum (50GB recommended)
- Stable internet connection

### **Deployment Commands**
```bash
# Clone repository
git clone <repository-url>
cd ha-ingestor

# Copy and configure environment
cp infrastructure/env.example .env
nano .env  # Edit with your configuration

# Start the system
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs -f
```

## 🔧 **Configuration**

### **Required Environment Variables**
```bash
# Home Assistant Configuration
HA_URL=ws://your-ha-instance:8123/api/websocket
HA_ACCESS_TOKEN=your_long_lived_access_token

# Weather API Configuration
WEATHER_API_KEY=your_openweathermap_api_key
WEATHER_LOCATION=your_city,country_code

# InfluxDB Configuration
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=your_organization
INFLUXDB_BUCKET=home_assistant

# API Configuration
API_KEY=your_secure_api_key
ENABLE_AUTH=true
```

## 🌐 **Access Points**

- **Admin Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8080/docs
- **Monitoring Dashboard**: http://localhost:8080/api/v1/monitoring/dashboard/overview
- **Health Checks**: http://localhost:8080/api/v1/health

## 📊 **System Architecture**

### **Services**
- **websocket-ingestion** - Home Assistant event capture
- **enrichment-pipeline** - Data enrichment and validation
- **data-retention** - Data lifecycle management
- **admin-api** - System administration API
- **health-dashboard** - Web-based administration interface
- **weather-api** - Weather data integration
- **influxdb** - Time-series database

### **Networking**
- **ha-ingestor-network** - Internal service communication
- **Port 3000** - Health dashboard frontend
- **Port 8080** - Admin API
- **Port 8086** - InfluxDB

## 🔍 **Monitoring & Maintenance**

### **Health Monitoring**
```bash
# Check service health
curl http://localhost:8080/api/v1/health

# View service logs
docker-compose logs -f websocket-ingestion
docker-compose logs -f enrichment-pipeline
docker-compose logs -f admin-api
```

### **System Management**
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart specific service
docker-compose restart websocket-ingestion

# View resource usage
docker stats
```

## 🛠️ **Troubleshooting**

### **Common Issues**
1. **WebSocket Connection Failed** - Check HA_URL and HA_ACCESS_TOKEN
2. **Weather API Errors** - Verify WEATHER_API_KEY and location
3. **InfluxDB Connection Issues** - Check database configuration
4. **High Memory Usage** - Monitor resource limits and adjust if needed

### **Log Analysis**
```bash
# View all logs
docker-compose logs

# Filter by service
docker-compose logs websocket-ingestion | grep ERROR

# Follow logs in real-time
docker-compose logs -f --tail=100
```

## 📈 **Performance Optimization**

### **Resource Limits**
- **CPU**: 2 cores minimum, 4 cores recommended
- **Memory**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum, 50GB recommended

### **Scaling Considerations**
- Monitor InfluxDB performance for high-volume data
- Adjust log retention policies based on storage capacity
- Configure alert thresholds based on system capacity

## 🔒 **Security**

### **Authentication**
- API key authentication for admin operations
- Token-based Home Assistant authentication
- Secure environment variable management

### **Network Security**
- Internal service communication only
- No external ports exposed except admin interface
- CORS configuration for web interface

## 📚 **Documentation**

- **User Guide**: Complete user manual
- **API Documentation**: OpenAPI/Swagger specs
- **CLI Reference**: Command-line tools
- **Troubleshooting**: Common issues and solutions

---

**🎉 Your Home Assistant Ingestor is now deployed and ready for production use!**
