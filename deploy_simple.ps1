# Simple Deployment Script for HA-Ingestor (No Docker Required)
# This script starts the HA-Ingestor service directly for immediate testing

Write-Host "🚀 Starting HA-Ingestor Simple Deployment..." -ForegroundColor Green

# Check if Python is available
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python is available: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Python is not available" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Python is not accessible" -ForegroundColor Red
    exit 1
}

# Check if ha_ingestor package is installed
Write-Host "🔍 Checking HA-Ingestor package..." -ForegroundColor Yellow
try {
    $importTest = python -c "import ha_ingestor; print('HA-Ingestor package found')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ HA-Ingestor package is available" -ForegroundColor Green
    } else {
        Write-Host "❌ HA-Ingestor package not found. Installing..." -ForegroundColor Yellow
        pip install -e .
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to install HA-Ingestor package" -ForegroundColor Red
            exit 1
        }
        Write-Host "✅ HA-Ingestor package installed successfully" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Failed to check HA-Ingestor package" -ForegroundColor Red
    exit 1
}

# Start the health server
Write-Host "🚀 Starting HA-Ingestor health server..." -ForegroundColor Yellow

# Create a simple startup script
$startupScript = @"
#!/usr/bin/env python3
"""
Simple startup script for HA-Ingestor health server.
"""

import asyncio
import uvicorn
from ha_ingestor.interfaces.health import HealthServer
from ha_ingestor.utils.logging import setup_default_logging

async def main():
    """Start the health server."""
    print("🚀 Starting HA-Ingestor Health Server...")

    # Setup logging
    setup_default_logging()

    # Create and start health server
    health_server = HealthServer(host="0.0.0.0", port=8000)
    app = health_server.create_app()

    print("✅ Health server created successfully")
    print("📋 Available endpoints:")
    print("   http://localhost:8000/health")
    print("   http://localhost:8000/health/dependencies")
    print("   http://localhost:8000/ready")
    print("   http://localhost:8000/metrics")
    print("   http://localhost:8000/api/events")
    print("   ws://localhost:8000/ws")
    print("")
    print("🌐 Server starting on http://localhost:8000")
    print("Press Ctrl+C to stop")

    # Start server
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        exit(1)
"@

# Write startup script to file
$startupScript | Out-File -FilePath "start_health_server.py" -Encoding UTF8

Write-Host "✅ Startup script created" -ForegroundColor Green

# Start the server
Write-Host "🚀 Starting server..." -ForegroundColor Yellow
Write-Host "   The server will start in a new window." -ForegroundColor Cyan
Write-Host "   You can access it at: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""

Start-Process -FilePath "python" -ArgumentList "start_health_server.py" -WindowStyle Normal

Write-Host "✅ HA-Ingestor service started!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Service URLs:" -ForegroundColor Cyan
Write-Host "   Health Check: http://localhost:8000/health" -ForegroundColor White
Write-Host "   Dependencies: http://localhost:8000/health/dependencies" -ForegroundColor White
Write-Host "   Metrics: http://localhost:8000/metrics" -ForegroundColor White
Write-Host "   Events API: http://localhost:8000/api/events" -ForegroundColor White
Write-Host "   WebSocket: ws://localhost:8000/ws" -ForegroundColor White
Write-Host ""
Write-Host "🔧 To stop the server, close the Python window or press Ctrl+C in that window" -ForegroundColor Yellow
Write-Host "🔧 To view logs, check the Python window output" -ForegroundColor Yellow
