#!/bin/bash

# InfluxDB Backup Script
# Creates comprehensive backups of InfluxDB data and configuration

set -e

# Configuration
INFLUXDB_URL="http://localhost:8086"
ORG_NAME="${INFLUXDB_ORG:-homeiq}"
ADMIN_TOKEN="${INFLUXDB_TOKEN:-homeiq-token}"
BACKUP_DIR="./backups/influxdb/$(date +%Y%m%d_%H%M%S)"

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

# Function to check if InfluxDB is accessible
check_influxdb_access() {
    print_status "Checking InfluxDB accessibility..."
    
    if ! curl -s -f "$INFLUXDB_URL/health" > /dev/null 2>&1; then
        print_error "InfluxDB is not accessible at $INFLUXDB_URL"
        exit 1
    fi
    
    print_success "InfluxDB is accessible"
}

# Function to create backup directory
create_backup_directory() {
    print_status "Creating backup directory: $BACKUP_DIR"
    
    mkdir -p "$BACKUP_DIR"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_error "Failed to create backup directory"
        exit 1
    fi
    
    print_success "Backup directory created"
}

# Function to backup InfluxDB configuration
backup_configuration() {
    print_status "Backing up InfluxDB configuration..."
    
    # Export organization info
    influx org list --host "$INFLUXDB_URL" --token "$ADMIN_TOKEN" --json > "$BACKUP_DIR/organizations.json"
    
    # Export bucket configurations
    influx bucket list --org "$ORG_NAME" --host "$INFLUXDB_URL" --token "$ADMIN_TOKEN" --json > "$BACKUP_DIR/buckets.json"
    
    # Export retention policies
    influx bucket list --org "$ORG_NAME" --host "$INFLUXDB_URL" --token "$ADMIN_TOKEN" --json | jq '.[] | {name: .name, retention: .retentionRules[0]}' > "$BACKUP_DIR/retention_policies.json"
    
    print_success "Configuration backed up"
}

# Function to backup data from each bucket
backup_bucket_data() {
    local bucket_name="$1"
    local days_back="${2:-30}"
    
    print_status "Backing up data from bucket: $bucket_name (last $days_back days)"
    
    local output_file="$BACKUP_DIR/${bucket_name}_data.csv"
    
    # Export data as CSV
    influx query \
        --org "$ORG_NAME" \
        --token "$ADMIN_TOKEN" \
        --host "$INFLUXDB_URL" \
        "from(bucket: \"$bucket_name\") |> range(start: -${days_back}d) |> to()" > "$output_file"
    
    # Check if file was created and has content
    if [ -f "$output_file" ] && [ -s "$output_file" ]; then
        local line_count=$(wc -l < "$output_file")
        print_success "Backed up $line_count lines from $bucket_name"
    else
        print_warning "No data found in $bucket_name for the last $days_back days"
        # Create empty file to indicate bucket was checked
        touch "$output_file"
        echo "# No data found in bucket $bucket_name for the last $days_back days" > "$output_file"
    fi
}

# Function to backup all bucket data
backup_all_buckets() {
    print_status "Backing up data from all buckets..."
    
    # Get list of buckets
    local buckets
    buckets=$(influx bucket list --org "$ORG_NAME" --host "$INFLUXDB_URL" --token "$ADMIN_TOKEN" --json | jq -r '.[].name')
    
    if [ -z "$buckets" ]; then
        print_warning "No buckets found to backup"
        return 0
    fi
    
    # Backup each bucket
    while IFS= read -r bucket; do
        if [ -n "$bucket" ]; then
            backup_bucket_data "$bucket"
        fi
    done <<< "$buckets"
    
    print_success "All buckets backed up"
}

# Function to backup Docker volumes
backup_docker_volumes() {
    print_status "Backing up Docker volumes..."
    
    # Check if volumes exist
    if docker volume ls | grep -q "homeiq_influxdb_data"; then
        print_status "Backing up InfluxDB data volume..."
        docker run --rm \
            -v homeiq_influxdb_data:/source:ro \
            -v "$(pwd)/$BACKUP_DIR":/backup \
            alpine tar czf /backup/influxdb_data_volume.tar.gz -C /source .
        print_success "InfluxDB data volume backed up"
    else
        print_warning "InfluxDB data volume not found"
    fi
    
    if docker volume ls | grep -q "homeiq_influxdb_config"; then
        print_status "Backing up InfluxDB config volume..."
        docker run --rm \
            -v homeiq_influxdb_config:/source:ro \
            -v "$(pwd)/$BACKUP_DIR":/backup \
            alpine tar czf /backup/influxdb_config_volume.tar.gz -C /source .
        print_success "InfluxDB config volume backed up"
    else
        print_warning "InfluxDB config volume not found"
    fi
}

# Function to create backup manifest
create_backup_manifest() {
    print_status "Creating backup manifest..."
    
    cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" << EOF
InfluxDB Backup Manifest
========================
Created: $(date)
InfluxDB URL: $INFLUXDB_URL
Organization: $ORG_NAME
Admin Token: $ADMIN_TOKEN

Backup Contents:
- organizations.json: Organization configuration
- buckets.json: Bucket configuration
- retention_policies.json: Retention policy settings
- *_data.csv: Data from each bucket
- influxdb_data_volume.tar.gz: Docker data volume backup
- influxdb_config_volume.tar.gz: Docker config volume backup

Restore Instructions:
1. Stop InfluxDB: docker compose stop influxdb
2. Restore volumes: docker run --rm -v homeiq_influxdb_data:/target -v \$(pwd)/$BACKUP_DIR:/backup alpine tar xzf /backup/influxdb_data_volume.tar.gz -C /target
3. Restore config: docker run --rm -v homeiq_influxdb_config:/target -v \$(pwd)/$BACKUP_DIR:/backup alpine tar xzf /backup/influxdb_config_volume.tar.gz -C /target
4. Start InfluxDB: docker compose up -d influxdb
5. Restore data: Use influx write commands with the CSV files

Notes:
- CSV files contain raw data exports
- Volume backups contain the complete InfluxDB state
- This backup is compatible with InfluxDB 2.7
EOF
    
    print_success "Backup manifest created"
}

# Function to display backup summary
display_backup_summary() {
    print_status "Backup Summary:"
    echo ""
    echo "📁 Backup Location: $BACKUP_DIR"
    echo "📊 Files Created:"
    
    if [ -d "$BACKUP_DIR" ]; then
        ls -la "$BACKUP_DIR" | grep -v "^total" | while read -r line; do
            echo "  $line"
        done
    fi
    
    echo ""
    echo "💾 Backup Size: $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "Unknown")"
    echo ""
    print_success "Backup completed successfully!"
}

# Main execution
main() {
    echo "💾 InfluxDB Backup Script"
    echo "========================"
    echo ""
    
    # Check prerequisites
    check_influxdb_access
    
    # Create backup directory
    create_backup_directory
    
    # Backup configuration
    backup_configuration
    
    # Backup data
    backup_all_buckets
    
    # Backup Docker volumes
    backup_docker_volumes
    
    # Create manifest
    create_backup_manifest
    
    # Display summary
    display_backup_summary
}

# Run main function
main "$@"
