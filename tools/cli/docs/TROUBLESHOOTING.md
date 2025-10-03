# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the HA Ingestor CLI tools.

## Common Issues

### 1. Connection Issues

#### Problem: "Cannot connect to Admin API"

**Symptoms:**
- Error message: "Cannot connect to Admin API"
- Commands fail with connection errors

**Possible Causes:**
- Admin API service is not running
- Wrong API URL configuration
- Network connectivity issues
- Firewall blocking connections

**Solutions:**

1. **Check if Admin API is running:**
   ```bash
   # Test basic connectivity
   curl http://localhost:8000/api/v1/health
   
   # Or use the CLI ping command
   ha-ingestor-cli system ping
   ```

2. **Verify configuration:**
   ```bash
   # Check current configuration
   ha-ingestor-cli config show
   
   # Update API URL if needed
   ha-ingestor-cli config set api_url http://localhost:8000
   ```

3. **Check Docker services:**
   ```bash
   # List running containers
   docker ps
   
   # Check Admin API logs
   docker logs ha-ingestor-admin-api
   ```

4. **Test network connectivity:**
   ```bash
   # Test TCP connection
   telnet localhost 8000
   
   # Or use the diagnostics command
   ha-ingestor-cli diagnostics connectivity
   ```

#### Problem: "Connection timeout"

**Symptoms:**
- Commands hang and eventually timeout
- Error message: "Request timeout"

**Solutions:**

1. **Increase timeout:**
   ```bash
   ha-ingestor-cli config set timeout 60
   ```

2. **Check system performance:**
   ```bash
   ha-ingestor-cli diagnostics performance --duration 30
   ```

3. **Check resource usage:**
   ```bash
   # Check Docker container resources
   docker stats ha-ingestor-admin-api
   ```

### 2. Authentication Issues

#### Problem: "Invalid API key"

**Symptoms:**
- Error message: "Invalid API key"
- 401 Unauthorized responses

**Solutions:**

1. **Check API token configuration:**
   ```bash
   ha-ingestor-cli config get api_token
   ```

2. **Set correct API token:**
   ```bash
   ha-ingestor-cli config set api_token your-actual-token
   ```

3. **Verify token in Admin API:**
   ```bash
   # Check Admin API configuration
   docker logs ha-ingestor-admin-api | grep -i token
   ```

4. **Generate new token if needed:**
   ```bash
   # Check Admin API documentation for token generation
   curl -X POST http://localhost:8000/api/v1/auth/token
   ```

### 3. Configuration Issues

#### Problem: "Configuration file not found"

**Symptoms:**
- Error message: "Configuration file not found"
- CLI uses default values

**Solutions:**

1. **Initialize configuration:**
   ```bash
   ha-ingestor-cli config init
   ```

2. **Specify config file:**
   ```bash
   ha-ingestor-cli --config /path/to/config.yaml system health
   ```

3. **Check environment variables:**
   ```bash
   echo $HA_INGESTOR_CONFIG
   ```

#### Problem: "Invalid configuration key"

**Symptoms:**
- Error message: "Invalid configuration key"
- Cannot set configuration values

**Solutions:**

1. **Check valid keys:**
   ```bash
   ha-ingestor-cli config show
   ```

2. **Use correct key names:**
   ```bash
   # Valid keys: api_url, api_token, timeout, retries, output_format, verbose
   ha-ingestor-cli config set api_url http://localhost:8000
   ```

### 4. Data Export Issues

#### Problem: "No events found"

**Symptoms:**
- Export commands return empty results
- Warning message: "No events found"

**Solutions:**

1. **Check time range:**
   ```bash
   # Try a longer time range
   ha-ingestor-cli export events --days 7
   ```

2. **Check event filters:**
   ```bash
   # List events first to see what's available
   ha-ingestor-cli events list --limit 10
   ```

3. **Verify system is processing events:**
   ```bash
   ha-ingestor-cli system stats
   ```

#### Problem: "Export file permission denied"

**Symptoms:**
- Error message: "Permission denied"
- Cannot write to output file

**Solutions:**

1. **Check file permissions:**
   ```bash
   ls -la output-file.json
   ```

2. **Use different output directory:**
   ```bash
   ha-ingestor-cli export events --output /tmp/events.json
   ```

3. **Create output directory:**
   ```bash
   mkdir -p ./exports
   ha-ingestor-cli export all --output-dir ./exports
   ```

### 5. Performance Issues

#### Problem: "Slow response times"

**Symptoms:**
- Commands take a long time to complete
- Timeout errors

**Solutions:**

1. **Run performance diagnostics:**
   ```bash
   ha-ingestor-cli diagnostics performance --duration 60
   ```

2. **Check system resources:**
   ```bash
   # Check Docker container resources
   docker stats
   
   # Check system resources
   top
   htop
   ```

3. **Optimize configuration:**
   ```bash
   # Increase timeout
   ha-ingestor-cli config set timeout 120
   
   # Reduce retry attempts
   ha-ingestor-cli config set retries 1
   ```

## Diagnostic Commands

### System Health Check

```bash
# Comprehensive health check
ha-ingestor-cli diagnostics check

# Quick status overview
ha-ingestor-cli system status

# Detailed health information
ha-ingestor-cli system health --format json
```

### Connectivity Testing

```bash
# Test all service connections
ha-ingestor-cli diagnostics connectivity

# Test API connection specifically
ha-ingestor-cli system ping

# Test with verbose output
ha-ingestor-cli --verbose system ping
```

### Performance Testing

```bash
# Run performance test for 60 seconds
ha-ingestor-cli diagnostics performance --duration 60

# Test with verbose output
ha-ingestor-cli --verbose diagnostics performance --duration 30
```

## Debug Mode

Enable verbose output for detailed debugging:

```bash
# Enable verbose mode globally
ha-ingestor-cli --verbose system health

# Enable verbose mode for specific command
ha-ingestor-cli system health --verbose
```

## Log Analysis

### CLI Logs

The CLI tool outputs logs to stdout/stderr. For persistent logging:

```bash
# Redirect output to file
ha-ingestor-cli system health > health.log 2>&1

# Append to log file
ha-ingestor-cli system stats >> system.log 2>&1
```

### Service Logs

Check service logs for underlying issues:

```bash
# Admin API logs
docker logs ha-ingestor-admin-api

# WebSocket Ingestion logs
docker logs ha-ingestor-websocket-ingestion

# All services logs
docker-compose logs
```

## Environment-Specific Issues

### Docker Environment

#### Problem: "Container not found"

**Solutions:**
```bash
# Check running containers
docker ps

# Start services
docker-compose up -d

# Check service status
docker-compose ps
```

#### Problem: "Port conflicts"

**Solutions:**
```bash
# Check port usage
netstat -tulpn | grep :8000

# Stop conflicting services
sudo systemctl stop conflicting-service

# Use different ports in docker-compose.yml
```

### Development Environment

#### Problem: "Module not found"

**Solutions:**
```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

## Getting Help

### Command Help

```bash
# General help
ha-ingestor-cli --help

# Command-specific help
ha-ingestor-cli system --help
ha-ingestor-cli events --help
ha-ingestor-cli config --help
```

### Version Information

```bash
# Show version
ha-ingestor-cli --version

# Show detailed version info
ha-ingestor-cli version
```

### Configuration Help

```bash
# Show current configuration
ha-ingestor-cli config show

# Show configuration in different formats
ha-ingestor-cli config show --format json
ha-ingestor-cli config show --format yaml
```

## Reporting Issues

When reporting issues, please include:

1. **CLI version:**
   ```bash
   ha-ingestor-cli --version
   ```

2. **System information:**
   ```bash
   ha-ingestor-cli diagnostics check
   ```

3. **Configuration:**
   ```bash
   ha-ingestor-cli config show --format json
   ```

4. **Error logs:**
   ```bash
   ha-ingestor-cli --verbose problematic-command > error.log 2>&1
   ```

5. **Environment details:**
   - Operating system
   - Python version
   - Docker version (if applicable)
   - Network configuration

## Prevention

### Best Practices

1. **Regular Health Checks:**
   ```bash
   # Set up regular health monitoring
   ha-ingestor-cli system health
   ```

2. **Configuration Backup:**
   ```bash
   # Backup configuration
   ha-ingestor-cli config show --format yaml > config-backup.yaml
   ```

3. **Data Export:**
   ```bash
   # Regular data exports
   ha-ingestor-cli export all --output-dir ./backups/$(date +%Y%m%d)
   ```

4. **Performance Monitoring:**
   ```bash
   # Regular performance checks
   ha-ingestor-cli diagnostics performance --duration 30
   ```
