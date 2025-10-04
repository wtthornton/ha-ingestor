# 📖 Home Assistant Ingestor - User Manual

## 🎯 **Getting Started**

### **What is Home Assistant Ingestor?**
Home Assistant Ingestor is a comprehensive system that captures, enriches, and stores Home Assistant events with weather context, providing real-time monitoring, data analysis, and production-ready deployment capabilities.

### **Key Features**
- **Real-time Event Capture** - Direct WebSocket connection to Home Assistant
- **Weather Enrichment** - Location-based weather data integration
- **Data Storage & Analysis** - InfluxDB time-series database
- **Web Dashboard** - Real-time monitoring and administration
- **Data Export** - Multiple formats (CSV, JSON, PDF, Excel)
- **Mobile Support** - Responsive design with touch gestures

## 🖥️ **Web Dashboard**

### **Accessing the Dashboard**
1. Open your web browser
2. Navigate to `http://localhost:3000`
3. The dashboard will load automatically

### **Dashboard Sections**

#### **1. System Health Overview**
- **Service Status** - Real-time status of all services
- **Connection Health** - WebSocket connection status
- **Event Metrics** - Events processed, error rates, processing latency
- **System Resources** - CPU, memory, disk usage

#### **2. Recent Events Feed**
- **Latest Events** - Most recent Home Assistant events
- **Event Details** - Entity ID, state changes, timestamps
- **Weather Context** - Weather data at time of event
- **Filtering** - Filter by entity, event type, time range

#### **3. Data Query Interface**
- **Time Range Selector** - Predefined and custom date ranges
- **Entity Filter** - Search and filter by specific entities
- **Weather Context Filter** - Filter by temperature and conditions
- **Export Options** - Download data in multiple formats

#### **4. Configuration Management**
- **Home Assistant Settings** - Connection configuration
- **Weather API Settings** - API key and location
- **Data Retention Policies** - Storage and cleanup settings
- **System Configuration** - Environment variables and settings

## 📊 **Monitoring & Alerts**

### **Real-time Monitoring**
- **Service Health** - Continuous monitoring of all services
- **Performance Metrics** - Real-time performance tracking
- **Error Tracking** - Error rates and failure patterns
- **Resource Usage** - System resource monitoring

### **Alerting System**
- **Configurable Alerts** - Set thresholds for critical metrics
- **Multiple Channels** - Email, Slack, Webhook notifications
- **Alert Management** - Acknowledge, resolve, and suppress alerts
- **Alert History** - Complete audit trail of all alerts

## 🔧 **Configuration**

### **Home Assistant Configuration**
1. **Generate Long-Lived Access Token**
   - Go to Home Assistant → Profile → Long-lived access tokens
   - Create a new token with appropriate permissions
   - Copy the token for configuration

2. **Configure Connection**
   - Set `HA_URL` to your Home Assistant WebSocket URL
   - Set `HA_ACCESS_TOKEN` to your long-lived token
   - Configure entity filters if needed

### **Weather API Configuration**
1. **Get OpenWeatherMap API Key**
   - Sign up at https://openweathermap.org/api
   - Generate an API key
   - Copy the key for configuration

2. **Set Location**
   - Configure `WEATHER_LOCATION` with your city and country
   - Format: "City,CountryCode" (e.g., "London,GB")

### **Data Retention Configuration**
1. **Retention Policies**
   - Set data retention periods (default: 1 year)
   - Configure cleanup intervals
   - Set storage limits and alerts

2. **Backup Settings**
   - Configure backup schedules
   - Set backup retention periods
   - Configure backup storage locations

## 📈 **Data Analysis**

### **Querying Data**
1. **Select Time Range**
   - Choose predefined ranges (hour, day, week, month)
   - Set custom date ranges
   - Apply time zone settings

2. **Filter Data**
   - Filter by specific entities
   - Filter by event types
   - Filter by weather conditions
   - Apply custom filters

3. **Export Data**
   - Export in CSV format for spreadsheet analysis
   - Export in JSON format for programmatic analysis
   - Export in PDF format for reports
   - Export in Excel format for advanced analysis

### **Visualization**
- **Event Patterns** - Visualize event frequency over time
- **Trend Analysis** - Identify patterns and trends
- **Weather Correlation** - Analyze weather impact on events
- **Performance Metrics** - Monitor system performance

## 🛠️ **Maintenance**

### **Regular Maintenance**
1. **Monitor System Health**
   - Check service status daily
   - Review error logs weekly
   - Monitor resource usage

2. **Data Management**
   - Review data retention policies monthly
   - Clean up old backups quarterly
   - Monitor storage usage

3. **Security Updates**
   - Keep Docker images updated
   - Review access tokens quarterly
   - Update API keys as needed

### **Troubleshooting**
1. **Service Issues**
   - Check service logs for errors
   - Verify configuration settings
   - Restart services if needed

2. **Connection Problems**
   - Verify Home Assistant connectivity
   - Check WebSocket connection status
   - Validate access tokens

3. **Performance Issues**
   - Monitor resource usage
   - Check for high error rates
   - Review data volume and retention

## 📱 **Mobile Access**

### **Mobile Dashboard**
- **Responsive Design** - Optimized for mobile devices
- **Touch Gestures** - Swipe, pinch, and tap support
- **Mobile Navigation** - Touch-friendly navigation
- **Offline Support** - Basic functionality when offline

### **Mobile Features**
- **Real-time Monitoring** - Mobile-optimized health dashboard
- **Event Notifications** - Push notifications for critical events
- **Quick Actions** - Mobile-friendly configuration updates
- **Data Export** - Mobile-optimized export functionality

## 🔒 **Security**

### **Access Control**
- **API Authentication** - Secure API key authentication
- **User Permissions** - Role-based access control
- **Session Management** - Secure session handling
- **Audit Trail** - Complete access logging

### **Data Protection**
- **Encrypted Storage** - Secure data storage
- **Secure Transmission** - Encrypted data transmission
- **Access Logging** - Complete audit trail
- **Backup Security** - Encrypted backup storage

## 📞 **Support**

### **Documentation**
- **API Documentation** - Complete API reference
- **Configuration Guide** - Detailed configuration instructions
- **Troubleshooting Guide** - Common issues and solutions
- **CLI Reference** - Command-line tool documentation

### **Getting Help**
1. **Check Documentation** - Review user manual and guides
2. **Check Logs** - Review system logs for errors
3. **Verify Configuration** - Ensure all settings are correct
4. **Contact Support** - Reach out for additional assistance

---

**🎉 Enjoy using your Home Assistant Ingestor system!**
