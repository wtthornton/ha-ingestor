#!/bin/bash

# InfluxDB Schema Reset & Validation Script
# This script resets InfluxDB and ensures the correct schema for hybrid architecture

set -e

echo "🔄 Starting InfluxDB Schema Reset & Validation..."

# Configuration
INFLUXDB_URL="http://localhost:8086"
ORG_NAME="${INFLUXDB_ORG:-homeiq}"
BUCKET_NAME="${INFLUXDB_BUCKET:-home_assistant_events}"
ADMIN_TOKEN="${INFLUXDB_TOKEN:-homeiq-token}"
USERNAME="${INFLUXDB_USERNAME:-admin}"
PASSWORD="${INFLUXDB_PASSWORD:-admin123}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for InfluxDB to be ready
wait_for_influxdb() {
    print_status "Waiting for InfluxDB to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$INFLUXDB_URL/health" > /dev/null 2>&1; then
            print_success "InfluxDB is ready!"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - InfluxDB not ready yet. Waiting..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    print_error "InfluxDB failed to start within expected time"
    exit 1
}

# Function to create organization
create_organization() {
    print_status "Creating organization: $ORG_NAME"
    
    # Check if organization already exists
    if influx org list --host "$INFLUXDB_URL" --token "$ADMIN_TOKEN" | grep -q "$ORG_NAME"; then
        print_warning "Organization '$ORG_NAME' already exists"
    else
        influx org create \
            --name "$ORG_NAME" \
            --description "Home Assistant Data Ingestion Organization" \
            --token "$ADMIN_TOKEN" \
            --host "$INFLUXDB_URL"
        print_success "Organization '$ORG_NAME' created"
    fi
}

# Function to create bucket with correct retention policy
create_bucket() {
    print_status "Creating bucket: $BUCKET_NAME with 365-day retention"
    
    # Check if bucket already exists
    if influx bucket list --org "$ORG_NAME" --host "$INFLUXDB_URL" --token "$ADMIN_TOKEN" | grep -q "$BUCKET_NAME"; then
        print_warning "Bucket '$BUCKET_NAME' already exists - removing and recreating"
        influx bucket delete \
            --name "$BUCKET_NAME" \
            --org "$ORG_NAME" \
            --token "$ADMIN_TOKEN" \
            --host "$INFLUXDB_URL"
    fi
    
    # Create bucket with 1-year retention (corrected from 30 days)
    influx bucket create \
        --name "$BUCKET_NAME" \
        --org "$ORG_NAME" \
        --retention 365d \
        --token "$ADMIN_TOKEN" \
        --host "$INFLUXDB_URL"
    
    print_success "Bucket '$BUCKET_NAME' created with 365-day retention"
}

# Function to create additional buckets for different data types
create_additional_buckets() {
    print_status "Creating additional buckets for hybrid architecture..."
    
    # Sports data bucket
    influx bucket create \
        --name "sports_data" \
        --org "$ORG_NAME" \
        --retention 90d \
        --token "$ADMIN_TOKEN" \
        --host "$INFLUXDB_URL"
    
    # Weather data bucket
    influx bucket create \
        --name "weather_data" \
        --org "$ORG_NAME" \
        --retention 180d \
        --token "$ADMIN_TOKEN" \
        --host "$INFLUXDB_URL"
    
    # System metrics bucket
    influx bucket create \
        --name "system_metrics" \
        --org "$ORG_NAME" \
        --retention 30d \
        --token "$ADMIN_TOKEN" \
        --host "$INFLUXDB_URL"
    
    print_success "Additional buckets created"
}

# Function to validate schema by creating test data points
validate_schema() {
    print_status "Validating schema with test data points..."
    
    # Create test data point with all expected tags and fields
    cat << EOF | influx write \
        --bucket "$BUCKET_NAME" \
        --org "$ORG_NAME" \
        --token "$ADMIN_TOKEN" \
        --host "$INFLUXDB_URL" \
        --precision ns
home_assistant_events,entity_id=sensor.living_room_temperature,domain=sensor,device_class=temperature,area=living_room,device_name="Living Room Temperature Sensor",device_id=zwave_001,area_id=room_001,entity_category=null,integration=zwave,weather_condition=clear,time_of_day=afternoon state_value="22.5",previous_state="22.3",normalized_value=22.5,unit_of_measurement="°C",confidence=0.95,context_id="ctx_001",context_parent_id="automation_001",context_user_id="user_001",duration_seconds=3600,energy_consumption=0.0,weather_temp=22.5,weather_humidity=45.0,weather_pressure=1013.25,manufacturer="Z-Wave Alliance",model="ZW100",sw_version="1.0.0" $(date +%s%N)
EOF
    
    print_success "Test data point created"
}

# Function to verify data was written correctly
verify_schema() {
    print_status "Verifying schema structure..."
    
    # Query the test data and check schema
    local schema_result
    schema_result=$(influx query \
        --org "$ORG_NAME" \
        --token "$ADMIN_TOKEN" \
        --host "$INFLUXDB_URL" \
        "from(bucket: \"$BUCKET_NAME\") |> range(start: -1h) |> limit(n:1) |> schema.fieldsAsCols()")
    
    if [ $? -eq 0 ]; then
        print_success "Schema verification completed"
        echo "$schema_result"
    else
        print_error "Schema verification failed"
        exit 1
    fi
}

# Function to clean up test data
cleanup_test_data() {
    print_status "Cleaning up test data..."
    
    # Delete the test data point
    influx delete \
        --bucket "$BUCKET_NAME" \
        --org "$ORG_NAME" \
        --token "$ADMIN_TOKEN" \
        --host "$INFLUXDB_URL" \
        --start "$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')" \
        --stop "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
        --predicate 'entity_id="sensor.living_room_temperature"'
    
    print_success "Test data cleaned up"
}

# Function to display final status
display_final_status() {
    print_status "Final InfluxDB Status:"
    echo ""
    echo "📊 Organization: $ORG_NAME"
    echo "📦 Buckets:"
    influx bucket list --org "$ORG_NAME" --host "$INFLUXDB_URL" --token "$ADMIN_TOKEN" --json | jq -r '.[] | "  - \(.name) (retention: \(.retentionRules[0].everySeconds // "infinite" | tonumber / 86400 | floor) days)"'
    echo ""
    echo "🔑 Admin Token: $ADMIN_TOKEN"
    echo "🌐 URL: $INFLUXDB_URL"
    echo ""
    print_success "InfluxDB reset and schema validation completed!"
}

# Main execution
main() {
    echo "🚀 InfluxDB Schema Reset & Validation Script"
    echo "=============================================="
    echo ""
    
    # Wait for InfluxDB to be ready
    wait_for_influxdb
    
    # Create organization
    create_organization
    
    # Create buckets
    create_bucket
    create_additional_buckets
    
    # Validate schema
    validate_schema
    verify_schema
    
    # Clean up test data
    cleanup_test_data
    
    # Display final status
    display_final_status
}

# Run main function
main "$@"
