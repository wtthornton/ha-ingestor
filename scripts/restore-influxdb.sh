#!/bin/bash

# InfluxDB Restore Script
# Restores InfluxDB data and configuration from backup

set -e

# Configuration
INFLUXDB_URL="http://localhost:8086"
ORG_NAME="${INFLUXDB_ORG:-homeiq}"
ADMIN_TOKEN="${INFLUXDB_TOKEN:-homeiq-token}"

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

# Function to display usage
usage() {
    echo "Usage: $0 <backup_directory>"
    echo ""
    echo "Example: $0 ./backups/influxdb/20250119_143022"
    echo ""
    echo "This script restores InfluxDB from a backup created by backup-influxdb.sh"
    exit 1
}

# Function to validate backup directory
validate_backup_directory() {
    local backup_dir="$1"
    
    if [ -z "$backup_dir" ]; then
        print_error "Backup directory not specified"
        usage
    fi
    
    if [ ! -d "$backup_dir" ]; then
        print_error "Backup directory does not exist: $backup_dir"
        exit 1
    fi
    
    if [ ! -f "$backup_dir/BACKUP_MANIFEST.txt" ]; then
        print_error "Invalid backup directory - BACKUP_MANIFEST.txt not found"
        exit 1
    fi
    
    print_success "Backup directory validated: $backup_dir"
}

# Function to stop InfluxDB
stop_influxdb() {
    print_status "Stopping InfluxDB..."
    
    docker compose stop influxdb
    
    if [ $? -eq 0 ]; then
        print_success "InfluxDB stopped"
    else
        print_error "Failed to stop InfluxDB"
        exit 1
    fi
}

# Function to restore Docker volumes
restore_docker_volumes() {
    local backup_dir="$1"
    
    print_status "Restoring Docker volumes..."
    
    # Remove existing volumes if they exist
    if docker volume ls | grep -q "homeiq_influxdb_data"; then
        print_status "Removing existing InfluxDB data volume..."
        docker volume rm homeiq_influxdb_data
    fi
    
    if docker volume ls | grep -q "homeiq_influxdb_config"; then
        print_status "Removing existing InfluxDB config volume..."
        docker volume rm homeiq_influxdb_config
    fi
    
    # Create new volumes
    print_status "Creating new InfluxDB volumes..."
    docker volume create homeiq_influxdb_data
    docker volume create homeiq_influxdb_config
    
    # Restore data volume
    if [ -f "$backup_dir/influxdb_data_volume.tar.gz" ]; then
        print_status "Restoring InfluxDB data volume..."
        docker run --rm \
            -v homeiq_influxdb_data:/target \
            -v "$(pwd)/$backup_dir":/backup \
            alpine tar xzf /backup/influxdb_data_volume.tar.gz -C /target
        print_success "InfluxDB data volume restored"
    else
        print_warning "InfluxDB data volume backup not found - using empty volume"
    fi
    
    # Restore config volume
    if [ -f "$backup_dir/influxdb_config_volume.tar.gz" ]; then
        print_status "Restoring InfluxDB config volume..."
        docker run --rm \
            -v homeiq_influxdb_config:/target \
            -v "$(pwd)/$backup_dir":/backup \
            alpine tar xzf /backup/influxdb_config_volume.tar.gz -C /target
        print_success "InfluxDB config volume restored"
    else
        print_warning "InfluxDB config volume backup not found - using empty volume"
    fi
}

# Function to start InfluxDB
start_influxdb() {
    print_status "Starting InfluxDB..."
    
    docker compose up -d influxdb
    
    # Wait for InfluxDB to be ready
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

# Function to restore organizations
restore_organizations() {
    local backup_dir="$1"
    
    print_status "Restoring organizations..."
    
    if [ -f "$backup_dir/organizations.json" ]; then
        # Parse organizations and create them
        jq -r '.[] | "\(.name)"' "$backup_dir/organizations.json" | while read -r org_name; do
            if [ -n "$org_name" ]; then
                print_status "Creating organization: $org_name"
                influx org create \
                    --name "$org_name" \
                    --description "Restored from backup" \
                    --token "$ADMIN_TOKEN" \
                    --host "$INFLUXDB_URL" || print_warning "Organization $org_name may already exist"
            fi
        done
        print_success "Organizations restored"
    else
        print_warning "Organizations backup not found - skipping"
    fi
}

# Function to restore buckets
restore_buckets() {
    local backup_dir="$1"
    
    print_status "Restoring buckets..."
    
    if [ -f "$backup_dir/buckets.json" ]; then
        # Parse buckets and create them
        jq -r '.[] | "\(.name)|\(.retentionRules[0].everySeconds // "infinite")"' "$backup_dir/buckets.json" | while IFS='|' read -r bucket_name retention_seconds; do
            if [ -n "$bucket_name" ]; then
                print_status "Creating bucket: $bucket_name"
                
                # Convert retention seconds to appropriate format
                local retention_flag=""
                if [ "$retention_seconds" != "infinite" ] && [ "$retention_seconds" != "null" ]; then
                    local retention_days=$((retention_seconds / 86400))
                    retention_flag="--retention ${retention_days}d"
                fi
                
                influx bucket create \
                    --name "$bucket_name" \
                    --org "$ORG_NAME" \
                    $retention_flag \
                    --token "$ADMIN_TOKEN" \
                    --host "$INFLUXDB_URL" || print_warning "Bucket $bucket_name may already exist"
            fi
        done
        print_success "Buckets restored"
    else
        print_warning "Buckets backup not found - skipping"
    fi
}

# Function to restore data
restore_data() {
    local backup_dir="$1"
    
    print_status "Restoring data..."
    
    # Find all CSV files in backup directory
    find "$backup_dir" -name "*_data.csv" -type f | while read -r csv_file; do
        local bucket_name=$(basename "$csv_file" _data.csv)
        
        # Skip if file is empty or contains only header/no data message
        if [ -s "$csv_file" ] && ! grep -q "No data found" "$csv_file"; then
            print_status "Restoring data to bucket: $bucket_name"
            
            # Convert CSV to line protocol format and write to InfluxDB
            # Note: This is a simplified approach - in practice, you might need more sophisticated CSV parsing
            tail -n +2 "$csv_file" | while IFS=',' read -r measurement tag_set field_set timestamp; do
                if [ -n "$measurement" ] && [ -n "$field_set" ]; then
                    echo "${measurement},${tag_set} ${field_set} ${timestamp}" | influx write \
                        --bucket "$bucket_name" \
                        --org "$ORG_NAME" \
                        --token "$ADMIN_TOKEN" \
                        --host "$INFLUXDB_URL" \
                        --precision ns
                fi
            done
            
            print_success "Data restored to bucket: $bucket_name"
        else
            print_warning "No data to restore for bucket: $bucket_name"
        fi
    done
}

# Function to verify restoration
verify_restoration() {
    local backup_dir="$1"
    
    print_status "Verifying restoration..."
    
    # Check if InfluxDB is accessible
    if ! curl -s -f "$INFLUXDB_URL/health" > /dev/null 2>&1; then
        print_error "InfluxDB is not accessible"
        return 1
    fi
    
    # List buckets
    print_status "Current buckets:"
    influx bucket list --org "$ORG_NAME" --host "$INFLUXDB_URL" --token "$ADMIN_TOKEN"
    
    # Check data in each bucket
    influx bucket list --org "$ORG_NAME" --host "$INFLUXDB_URL" --token "$ADMIN_TOKEN" --json | jq -r '.[].name' | while read -r bucket_name; do
        if [ -n "$bucket_name" ]; then
            local count=$(influx query \
                --org "$ORG_NAME" \
                --token "$ADMIN_TOKEN" \
                --host "$INFLUXDB_URL" \
                "from(bucket: \"$bucket_name\") |> range(start: -30d) |> count()" 2>/dev/null | grep -o '[0-9]*' | tail -1 || echo "0")
            
            if [ "$count" -gt 0 ]; then
                print_success "Bucket $bucket_name contains $count records"
            else
                print_warning "Bucket $bucket_name contains no records"
            fi
        fi
    done
    
    print_success "Restoration verification completed"
}

# Function to display restoration summary
display_restoration_summary() {
    local backup_dir="$1"
    
    print_status "Restoration Summary:"
    echo ""
    echo "📁 Restored From: $backup_dir"
    echo "🌐 InfluxDB URL: $INFLUXDB_URL"
    echo "🏢 Organization: $ORG_NAME"
    echo ""
    print_success "InfluxDB restoration completed successfully!"
}

# Main execution
main() {
    local backup_dir="$1"
    
    echo "🔄 InfluxDB Restore Script"
    echo "=========================="
    echo ""
    
    # Validate backup directory
    validate_backup_directory "$backup_dir"
    
    # Stop InfluxDB
    stop_influxdb
    
    # Restore Docker volumes
    restore_docker_volumes "$backup_dir"
    
    # Start InfluxDB
    start_influxdb
    
    # Restore organizations
    restore_organizations "$backup_dir"
    
    # Restore buckets
    restore_buckets "$backup_dir"
    
    # Restore data
    restore_data "$backup_dir"
    
    # Verify restoration
    verify_restoration "$backup_dir"
    
    # Display summary
    display_restoration_summary "$backup_dir"
}

# Run main function
main "$@"
