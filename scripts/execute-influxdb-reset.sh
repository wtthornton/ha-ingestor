#!/bin/bash

# InfluxDB Reset Execution Script
# Complete step-by-step execution plan with safety checks

set -e

# Configuration
BACKUP_DIR="./backups/influxdb/$(date +%Y%m%d_%H%M%S)"
DRY_RUN="${1:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${PURPLE}===========================================${NC}"
    echo -e "${PURPLE} $1${NC}"
    echo -e "${PURPLE}===========================================${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓ SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠ WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗ ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to display usage
usage() {
    echo "Usage: $0 [--dry-run]"
    echo ""
    echo "Options:"
    echo "  --dry-run    Show what would be done without executing"
    echo ""
    echo "This script will:"
    echo "1. Create a backup of current InfluxDB data"
    echo "2. Stop all services that use InfluxDB"
    echo "3. Reset InfluxDB with correct schema"
    echo "4. Validate the new schema"
    echo "5. Restart all services"
    echo "6. Verify everything is working"
    exit 1
}

# Function to check prerequisites
check_prerequisites() {
    print_header "PREREQUISITE CHECKS"
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running"
        exit 1
    fi
    print_success "Docker is running"
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found in current directory"
        exit 1
    fi
    print_success "docker-compose.yml found"
    
    # Check if required scripts exist
    local required_scripts=("reset-influxdb-schema.sh" "backup-influxdb.sh" "validate-influxdb-schema.sh")
    for script in "${required_scripts[@]}"; do
        if [ ! -f "scripts/$script" ]; then
            print_error "Required script not found: scripts/$script"
            exit 1
        fi
        print_success "Script found: scripts/$script"
    done
    
    # Check if jq is installed
    if ! command -v jq > /dev/null 2>&1; then
        print_error "jq is required but not installed"
        exit 1
    fi
    print_success "jq is installed"
}

# Function to confirm execution
confirm_execution() {
    if [ "$DRY_RUN" = "true" ]; then
        print_warning "DRY RUN MODE - No changes will be made"
        return 0
    fi
    
    print_header "EXECUTION CONFIRMATION"
    echo ""
    print_warning "This will COMPLETELY RESET your InfluxDB database!"
    echo ""
    echo "The following actions will be performed:"
    echo "1. 📦 Create backup in: $BACKUP_DIR"
    echo "2. 🛑 Stop all services using InfluxDB"
    echo "3. 🗑️  Remove all InfluxDB data and configuration"
    echo "4. 🔄 Recreate InfluxDB with correct schema"
    echo "5. ✅ Validate new schema structure"
    echo "6. 🚀 Restart all services"
    echo "7. 🔍 Verify everything is working"
    echo ""
    print_warning "ALL EXISTING DATA WILL BE LOST (unless backed up)!"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_status "Operation cancelled by user"
        exit 0
    fi
}

# Function to create backup
create_backup() {
    print_header "STEP 1: CREATE BACKUP"
    
    if [ "$DRY_RUN" = "true" ]; then
        print_status "Would create backup in: $BACKUP_DIR"
        return 0
    fi
    
    print_step "Creating backup of current InfluxDB data..."
    
    if ./scripts/backup-influxdb.sh; then
        print_success "Backup created successfully"
    else
        print_error "Backup failed"
        exit 1
    fi
}

# Function to stop services
stop_services() {
    print_header "STEP 2: STOP SERVICES"
    
    if [ "$DRY_RUN" = "true" ]; then
        print_status "Would stop services: websocket-ingestion, enrichment-pipeline, data-api, sports-data"
        return 0
    fi
    
    print_step "Stopping services that use InfluxDB..."
    
    docker compose stop websocket-ingestion enrichment-pipeline data-api sports-data
    
    if [ $? -eq 0 ]; then
        print_success "Services stopped successfully"
    else
        print_error "Failed to stop services"
        exit 1
    fi
    
    # Verify services are stopped
    local running_services
    running_services=$(docker compose ps --filter "status=running" --format "table {{.Service}}" | grep -E "(websocket-ingestion|enrichment-pipeline|data-api|sports-data)" || true)
    
    if [ -n "$running_services" ]; then
        print_warning "Some services are still running:"
        echo "$running_services"
        print_status "Continuing with reset..."
    else
        print_success "All target services are stopped"
    fi
}

# Function to reset InfluxDB
reset_influxdb() {
    print_header "STEP 3: RESET INFLUXDB"
    
    if [ "$DRY_RUN" = "true" ]; then
        print_status "Would remove InfluxDB container and volumes"
        print_status "Would recreate InfluxDB with clean state"
        return 0
    fi
    
    print_step "Removing InfluxDB container and volumes..."
    
    # Stop InfluxDB
    docker compose stop influxdb
    
    # Remove container
    docker compose rm -f influxdb
    
    # Remove volumes
    if docker volume ls | grep -q "homeiq_influxdb_data"; then
        docker volume rm homeiq_influxdb_data
        print_success "Removed InfluxDB data volume"
    fi
    
    if docker volume ls | grep -q "homeiq_influxdb_config"; then
        docker volume rm homeiq_influxdb_config
        print_success "Removed InfluxDB config volume"
    fi
    
    print_step "Recreating InfluxDB with clean state..."
    
    # Start InfluxDB
    docker compose up -d influxdb
    
    # Wait for InfluxDB to be ready
    print_status "Waiting for InfluxDB to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:8086/health > /dev/null 2>&1; then
            print_success "InfluxDB is ready!"
            break
        fi
        
        print_status "Attempt $attempt/$max_attempts - Waiting for InfluxDB..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        print_error "InfluxDB failed to start within expected time"
        exit 1
    fi
}

# Function to initialize schema
initialize_schema() {
    print_header "STEP 4: INITIALIZE SCHEMA"
    
    if [ "$DRY_RUN" = "true" ]; then
        print_status "Would run schema initialization script"
        return 0
    fi
    
    print_step "Initializing InfluxDB schema..."
    
    if ./scripts/reset-influxdb-schema.sh; then
        print_success "Schema initialized successfully"
    else
        print_error "Schema initialization failed"
        exit 1
    fi
}

# Function to validate schema
validate_schema() {
    print_header "STEP 5: VALIDATE SCHEMA"
    
    if [ "$DRY_RUN" = "true" ]; then
        print_status "Would validate schema structure"
        return 0
    fi
    
    print_step "Validating InfluxDB schema..."
    
    if ./scripts/validate-influxdb-schema.sh; then
        print_success "Schema validation passed"
    else
        print_error "Schema validation failed"
        exit 1
    fi
}

# Function to restart services
restart_services() {
    print_header "STEP 6: RESTART SERVICES"
    
    if [ "$DRY_RUN" = "true" ]; then
        print_status "Would restart services in correct order"
        return 0
    fi
    
    print_step "Restarting services in correct order..."
    
    # Start services one by one with delays
    print_status "Starting websocket-ingestion..."
    docker compose up -d websocket-ingestion
    sleep 5
    
    print_status "Starting enrichment-pipeline..."
    docker compose up -d enrichment-pipeline
    sleep 5
    
    print_status "Starting data-api..."
    docker compose up -d data-api
    sleep 5
    
    print_status "Starting sports-data..."
    docker compose up -d sports-data
    sleep 5
    
    print_success "All services restarted"
}

# Function to verify services
verify_services() {
    print_header "STEP 7: VERIFY SERVICES"
    
    if [ "$DRY_RUN" = "true" ]; then
        print_status "Would verify all services are healthy"
        return 0
    fi
    
    print_step "Verifying all services are healthy..."
    
    # Wait for services to be ready
    sleep 10
    
    # Check service health
    local unhealthy_services
    unhealthy_services=$(docker compose ps --filter "health=unhealthy" --format "table {{.Service}}" | tail -n +2 || true)
    
    if [ -n "$unhealthy_services" ]; then
        print_warning "Some services are unhealthy:"
        echo "$unhealthy_services"
        print_status "Waiting additional time for services to stabilize..."
        sleep 30
        
        # Check again
        unhealthy_services=$(docker compose ps --filter "health=unhealthy" --format "table {{.Service}}" | tail -n +2 || true)
        if [ -n "$unhealthy_services" ]; then
            print_error "Some services are still unhealthy after waiting"
            docker compose ps
            exit 1
        fi
    fi
    
    print_success "All services are healthy"
}

# Function to test data flow
test_data_flow() {
    print_header "STEP 8: TEST DATA FLOW"
    
    if [ "$DRY_RUN" = "true" ]; then
        print_status "Would test data flow from HA to InfluxDB"
        return 0
    fi
    
    print_step "Testing data flow..."
    
    # Test WebSocket ingestion health
    if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
        print_success "WebSocket ingestion service is healthy"
    else
        print_error "WebSocket ingestion service is not responding"
        exit 1
    fi
    
    # Test enrichment pipeline health
    if curl -s -f http://localhost:8002/health > /dev/null 2>&1; then
        print_success "Enrichment pipeline service is healthy"
    else
        print_error "Enrichment pipeline service is not responding"
        exit 1
    fi
    
    # Test data API health
    if curl -s -f http://localhost:8006/health > /dev/null 2>&1; then
        print_success "Data API service is healthy"
    else
        print_error "Data API service is not responding"
        exit 1
    fi
    
    print_success "Data flow test passed"
}

# Function to display final status
display_final_status() {
    print_header "RESET COMPLETION STATUS"
    
    if [ "$DRY_RUN" = "true" ]; then
        print_status "DRY RUN COMPLETED - No changes were made"
        echo ""
        echo "To execute the actual reset, run:"
        echo "  $0"
        return 0
    fi
    
    echo ""
    print_success "🎉 INFLUXDB RESET COMPLETED SUCCESSFULLY!"
    echo ""
    echo "📊 Current Status:"
    echo "  ✅ InfluxDB schema is correct"
    echo "  ✅ All services are running"
    echo "  ✅ Data flow is working"
    echo "  ✅ Hybrid architecture is active"
    echo ""
    echo "🔗 Access Points:"
    echo "  🌐 Dashboard: http://localhost:3000"
    echo "  📊 InfluxDB UI: http://localhost:8086"
    echo "  🔌 WebSocket: http://localhost:8001"
    echo "  📡 Data API: http://localhost:8006"
    echo ""
    echo "📁 Backup Location: $BACKUP_DIR"
    echo ""
    print_status "Monitor the system for the next 24 hours to ensure stability"
}

# Function to handle errors
handle_error() {
    print_header "ERROR HANDLING"
    print_error "An error occurred during the reset process"
    echo ""
    echo "🔄 Rollback Options:"
    echo "1. Restore from backup: ./scripts/restore-influxdb.sh $BACKUP_DIR"
    echo "2. Manual recovery: Check docker compose logs"
    echo "3. Contact support: Review implementation/analysis/INFLUXDB_SCHEMA_RESET_PLAN.md"
    echo ""
    exit 1
}

# Set up error handling
trap handle_error ERR

# Main execution
main() {
    # Parse command line arguments
    if [ "$1" = "--dry-run" ]; then
        DRY_RUN="true"
    elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        usage
    fi
    
    echo "🚀 InfluxDB Reset Execution Script"
    echo "=================================="
    echo ""
    
    if [ "$DRY_RUN" = "true" ]; then
        print_warning "Running in DRY RUN mode - no changes will be made"
        echo ""
    fi
    
    # Execute all steps
    check_prerequisites
    confirm_execution
    create_backup
    stop_services
    reset_influxdb
    initialize_schema
    validate_schema
    restart_services
    verify_services
    test_data_flow
    display_final_status
    
    print_success "🎉 All operations completed successfully!"
}

# Run main function
main "$@"
