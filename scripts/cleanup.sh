#!/bin/bash

# Cleanup Script
# This script cleans up Docker containers, images, and volumes

set -e

echo "HA Ingestor Cleanup Script"
echo "=========================="

# Function to clean up development environment
cleanup_dev() {
    echo "Cleaning up development environment..."
    docker-compose -f docker-compose.dev.yml down -v
    echo "✅ Development environment cleaned up"
}

# Function to clean up production environment
cleanup_prod() {
    echo "Cleaning up production environment..."
    docker-compose -f docker-compose.prod.yml down -v
    echo "✅ Production environment cleaned up"
}

# Function to clean up all environments
cleanup_all() {
    echo "Cleaning up all environments..."
    docker-compose -f docker-compose.dev.yml down -v
    docker-compose -f docker-compose.prod.yml down -v
    echo "✅ All environments cleaned up"
}

# Function to remove unused Docker resources
cleanup_docker() {
    echo "Cleaning up unused Docker resources..."
    docker system prune -f
    echo "✅ Unused Docker resources cleaned up"
}

# Function to remove all project images
cleanup_images() {
    echo "Removing project images..."
    docker images | grep homeiq | awk '{print $3}' | xargs -r docker rmi -f
    echo "✅ Project images removed"
}

# Main menu
echo "Select cleanup option:"
echo "1. Clean up development environment"
echo "2. Clean up production environment"
echo "3. Clean up all environments"
echo "4. Clean up unused Docker resources"
echo "5. Remove project images"
echo "6. Full cleanup (all of the above)"
echo "7. Exit"

read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        cleanup_dev
        ;;
    2)
        cleanup_prod
        ;;
    3)
        cleanup_all
        ;;
    4)
        cleanup_docker
        ;;
    5)
        cleanup_images
        ;;
    6)
        cleanup_all
        cleanup_docker
        cleanup_images
        echo "🎉 Full cleanup completed!"
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
