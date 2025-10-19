#!/bin/bash

# InfluxDB Initialization Script
# This script sets up the initial InfluxDB configuration

set -e

echo "Initializing InfluxDB..."

# Wait for InfluxDB to be ready
echo "Waiting for InfluxDB to be ready..."
until curl -f http://localhost:8086/health; do
  echo "InfluxDB is not ready yet. Waiting..."
  sleep 5
done

echo "InfluxDB is ready!"

# Create organization and bucket if they don't exist
echo "Setting up organization and bucket..."

# Use influx CLI to create organization and bucket
influx org create \
  --name "${INFLUXDB_ORG:-homeiq}" \
  --description "Home Assistant Data Ingestion Organization" \
  --token "${INFLUXDB_TOKEN:-homeiq-token}" \
  --host http://localhost:8086

influx bucket create \
  --name "${INFLUXDB_BUCKET:-home_assistant_events}" \
  --org "${INFLUXDB_ORG:-homeiq}" \
  --retention 30d \
  --token "${INFLUXDB_TOKEN:-homeiq-token}" \
  --host http://localhost:8086

echo "InfluxDB initialization complete!"
