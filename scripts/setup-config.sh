#!/bin/bash
# Setup configuration files for HA Ingestor
# Creates .env files from templates

set -e

echo "🔧 HA Ingestor Configuration Setup"
echo "===================================="
echo ""

cd "$(dirname "$0")/.."

# Check if infrastructure directory exists
if [ ! -d "infrastructure" ]; then
    echo "❌ Error: infrastructure directory not found"
    exit 1
fi

cd infrastructure

# Function to setup config file
setup_config() {
    local template="$1"
    local target="$2"
    
    if [ ! -f "$template" ]; then
        echo "⚠️  Warning: Template $template not found, skipping"
        return
    fi
    
    if [ -f "$target" ]; then
        echo "⚠️  $target already exists, skipping (use --force to overwrite)"
        return
    fi
    
    cp "$template" "$target"
    chmod 600 "$target"
    echo "✅ Created $target (permissions: 600)"
}

# Setup configuration files
echo "Creating configuration files from templates..."
echo ""

setup_config "env.websocket.template" ".env.websocket"
setup_config "env.weather.template" ".env.weather"
setup_config "env.influxdb.template" ".env.influxdb"

echo ""
echo "✅ Configuration setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit configuration files in infrastructure/ directory"
echo "2. Or use the dashboard: http://localhost:3000/configuration"
echo "3. Start services: docker-compose up -d"
echo ""
echo "Configuration files:"
echo "  - infrastructure/.env.websocket  (Home Assistant)"
echo "  - infrastructure/.env.weather    (Weather API)"
echo "  - infrastructure/.env.influxdb   (Database)"
echo ""

