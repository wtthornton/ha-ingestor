# HA Ingestor CLI Tools

Command-line interface for managing and monitoring the Home Assistant Ingestor system.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install CLI Tool

```bash
pip install -e .
```

## Configuration

### Initial Setup

Initialize the CLI configuration:

```bash
ha-ingestor-cli config init --api-url http://localhost:8000 --api-token your-token
```

### Configuration File

The CLI tool looks for configuration in the following order:

1. Command-line `--config` option
2. `HA_INGESTOR_CONFIG` environment variable
3. `~/.ha-ingestor/config.yaml`
4. `./ha-ingestor.yaml`
5. `./.ha-ingestor.yaml`

### Environment Variables

- `HA_INGESTOR_API_URL`: Admin API URL (default: http://localhost:8000)
- `HA_INGESTOR_API_TOKEN`: API authentication token
- `HA_INGESTOR_TIMEOUT`: Request timeout in seconds (default: 30)
- `HA_INGESTOR_RETRIES`: Number of retry attempts (default: 3)
- `HA_INGESTOR_OUTPUT_FORMAT`: Default output format (default: table)
- `HA_INGESTOR_VERBOSE`: Enable verbose output (default: false)

## Usage

### Basic Commands

```bash
# Show version information
ha-ingestor-cli --version

# Show help
ha-ingestor-cli --help

# Show system information
ha-ingestor-cli info

# Show quick status
ha-ingestor-cli status
```

### System Management

```bash
# Check system health
ha-ingestor-cli system health

# Get system statistics
ha-ingestor-cli system stats

# Get quick status overview
ha-ingestor-cli system status

# Test API connection
ha-ingestor-cli system ping
```

### Events Management

```bash
# List recent events
ha-ingestor-cli events list

# List events with filters
ha-ingestor-cli events list --entity-id sensor.temperature --limit 50

# Search events
ha-ingestor-cli events search "temperature"

# Monitor events in real-time
ha-ingestor-cli events monitor --interval 5

# Export events
ha-ingestor-cli events export --format csv --output events.csv
```

### Configuration Management

```bash
# Show current configuration
ha-ingestor-cli config show

# Get specific configuration value
ha-ingestor-cli config get api_url

# Set configuration value
ha-ingestor-cli config set api_url http://new-url:8000

# Initialize configuration
ha-ingestor-cli config init

# Get remote system configuration
ha-ingestor-cli config remote

# Update remote configuration
ha-ingestor-cli config update config.json
```

### Data Export

```bash
# Export events
ha-ingestor-cli export events --format json --output events.json

# Export statistics
ha-ingestor-cli export stats --format yaml --output stats.yaml

# Export health status
ha-ingestor-cli export health --format json --output health.json

# Export all data
ha-ingestor-cli export all --output-dir ./export
```

### System Diagnostics

```bash
# Run comprehensive diagnostics
ha-ingestor-cli diagnostics check

# Test connectivity to all services
ha-ingestor-cli diagnostics connectivity

# Test system performance
ha-ingestor-cli diagnostics performance --duration 60
```

## Output Formats

The CLI supports multiple output formats:

- `table`: Human-readable table format (default)
- `json`: JSON format
- `yaml`: YAML format

Example:

```bash
ha-ingestor-cli system health --format json
ha-ingestor-cli events list --format yaml
```

## Examples

### Monitor System Health

```bash
# Check overall system health
ha-ingestor-cli system health

# Get detailed statistics
ha-ingestor-cli system stats

# Test connectivity
ha-ingestor-cli diagnostics connectivity
```

### Export Data for Analysis

```bash
# Export last 24 hours of events
ha-ingestor-cli export events --hours 24 --format csv --output events_24h.csv

# Export all data
ha-ingestor-cli export all --output-dir ./backup

# Export specific entity events
ha-ingestor-cli export events --entity-id sensor.temperature --format json --output temp_events.json
```

### Troubleshooting

```bash
# Run comprehensive diagnostics
ha-ingestor-cli diagnostics check

# Test API connectivity
ha-ingestor-cli system ping

# Check configuration
ha-ingestor-cli config show

# Monitor events in real-time
ha-ingestor-cli events monitor
```

## Error Handling

The CLI tool provides detailed error messages and exit codes:

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Connection error
- `4`: Authentication error

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_main.py

# Run with coverage
pytest --cov=src
```

### Adding New Commands

1. Create a new command file in `src/commands/`
2. Define the Typer app and commands
3. Add the command to `src/main.py`
4. Create tests in `tests/`
5. Update documentation

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check if the Admin API is running and accessible
2. **Authentication Error**: Verify the API token is correct
3. **Configuration Not Found**: Run `ha-ingestor-cli config init` to create initial configuration
4. **Permission Denied**: Ensure the CLI has write permissions for configuration files

### Debug Mode

Enable verbose output for debugging:

```bash
ha-ingestor-cli --verbose system health
```

### Log Files

The CLI tool logs to stdout/stderr. For persistent logging, redirect output:

```bash
ha-ingestor-cli system health > health.log 2>&1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
