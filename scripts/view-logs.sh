#!/bin/bash

# Log Viewing Script
# This script helps view logs from Docker containers

set -e

echo "HA Ingestor Log Viewer"
echo "====================="

# Function to show logs for a specific service
show_service_logs() {
    local service_name=$1
    echo "Showing logs for $service_name..."
    docker-compose logs -f --tail=100 "$service_name"
}

# Function to show logs for all services
show_all_logs() {
    echo "Showing logs for all services..."
    docker-compose logs -f --tail=50
}

# Function to show logs with timestamps
show_logs_with_timestamps() {
    local service_name=$1
    echo "Showing logs with timestamps for $service_name..."
    docker-compose logs -f --tail=100 -t "$service_name"
}

# Main menu
echo "Select an option:"
echo "1. View logs for all services"
echo "2. View logs for websocket-ingestion service"
echo "3. View logs for weather-api service"
echo "4. View logs for admin-api service"
echo "5. View logs for influxdb service"
echo "6. View logs with timestamps for all services"
echo "7. Exit"

read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        show_all_logs
        ;;
    2)
        show_service_logs "websocket-ingestion"
        ;;
    3)
        show_service_logs "weather-api"
        ;;
    4)
        show_service_logs "admin-api"
        ;;
    5)
        show_service_logs "influxdb"
        ;;
    6)
        show_logs_with_timestamps ""
        ;;
    7)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac
