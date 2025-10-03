# Deployment Architecture

### Deployment Strategy

**Frontend Deployment:**
- **Platform:** Docker container with nginx
- **Build Command:** `npm run build`
- **Output Directory:** `dist/`
- **CDN/Edge:** Local nginx serving static files

**Backend Deployment:**
- **Platform:** Docker containers orchestrated by Docker Compose
- **Build Command:** Docker multi-stage builds
- **Deployment Method:** Docker Compose with health checks and restart policies

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      influxdb:
        image: influxdb:2.7
        ports:
          - 8086:8086

    steps:
    - uses: actions/checkout@v4
    - name: Run tests
      run: |
        docker-compose -f docker-compose.yml build
        docker-compose -f docker-compose.yml up -d
        sleep 30
        docker-compose -f docker-compose.yml run --rm test-integration
        docker-compose -f docker-compose.yml down
```

### Environments

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|--------------|-------------|---------|
| Development | http://localhost:3000 | http://localhost:8080 | Local development |
| Production | http://ha-ingestor.local:3000 | http://ha-ingestor.local:8080 | Live environment |
