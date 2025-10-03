#!/bin/bash

# Production Environment Setup Script
# This script helps configure the production environment

set -e

echo "HA Ingestor Production Environment Setup"
echo "========================================"
echo ""

# Check if .env exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Backing up to .env.backup"
    cp .env .env.backup
fi

# Copy production template
echo "📋 Creating production environment configuration..."
cp infrastructure/env.production .env

echo ""
echo "🔧 CONFIGURATION REQUIRED"
echo "========================="
echo ""
echo "You need to configure the following values in .env:"
echo ""
echo "1. HOME_ASSISTANT_TOKEN - Get from Home Assistant > Profile > Long-lived access tokens"
echo "2. INFLUXDB_PASSWORD - Choose a secure password for InfluxDB"
echo "3. INFLUXDB_TOKEN - Choose a secure token for InfluxDB API access"
echo "4. JWT_SECRET_KEY - Generate a secure random string for JWT signing"
echo "5. ADMIN_PASSWORD - Choose a secure password for admin access"
echo "6. WEATHER_API_KEY - (Optional) Get from OpenWeatherMap API"
echo ""
echo "To generate secure tokens, you can use:"
echo "  openssl rand -base64 32"
echo ""
echo "After configuration, test with:"
echo "  ./scripts/test-services.sh"
echo ""
echo "✅ Environment template created at .env"
echo "📝 Please edit .env with your production values"
