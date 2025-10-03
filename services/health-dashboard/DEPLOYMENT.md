# Health Dashboard Deployment Guide

This document provides comprehensive instructions for building and deploying the Health Dashboard frontend application.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Build Process](#build-process)
- [Docker Deployment](#docker-deployment)
- [Environment Configuration](#environment-configuration)
- [Performance Optimization](#performance-optimization)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Node.js 18+ and npm
- Docker and Docker Compose
- Git (for version tracking)

## Build Process

### Development Build

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm run test

# Run tests with coverage
npm run test:coverage
```

### Production Build

```bash
# Clean and build
npm run build

# Build with bundle analysis
npm run build:analyze

# Preview production build
npm run preview:prod
```

### Build Scripts

The build process includes several optimization steps:

1. **Type Checking**: TypeScript compilation with strict type checking
2. **Code Splitting**: Automatic chunk splitting for optimal loading
3. **Asset Optimization**: Image compression and CSS minification
4. **Bundle Analysis**: Size analysis and optimization recommendations
5. **Security Headers**: CSP and security header injection

## Docker Deployment

### Multi-Stage Build

The Dockerfile uses a multi-stage build process:

1. **Dependencies Stage**: Install production dependencies
2. **Builder Stage**: Compile and build the application
3. **Production Stage**: Serve with optimized Nginx

### Building Docker Image

```bash
# Build production image
docker build -t health-dashboard:latest .

# Build with specific tag
docker build -t health-dashboard:v1.0.0 .

# Build development image
docker build -f Dockerfile.dev -t health-dashboard:dev .
```

### Docker Compose Integration

The health dashboard is integrated into the main Docker Compose setup:

```yaml
health-dashboard:
  build:
    context: ./services/health-dashboard
    dockerfile: Dockerfile
  container_name: ha-ingestor-dashboard
  restart: unless-stopped
  ports:
    - "3000:80"
  environment:
    - VITE_API_BASE_URL=http://localhost:8000/api/v1
  depends_on:
    admin-api:
      condition: service_healthy
  networks:
    - ha-ingestor-network
```

## Environment Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_ENVIRONMENT` | Build environment | `production` | No |
| `VITE_API_BASE_URL` | API base URL | `/api/v1` | No |
| `VITE_WS_URL` | WebSocket URL | `ws://localhost:8000/ws` | No |
| `VITE_PORT` | Development port | `3000` | No |
| `VITE_BASE_URL` | Application base URL | `/` | No |

### Environment Files

- `env.development`: Development configuration
- `env.production`: Production configuration

## Performance Optimization

### Build Optimizations

1. **Code Splitting**: Automatic vendor and feature chunking
2. **Tree Shaking**: Dead code elimination
3. **Minification**: JavaScript and CSS compression
4. **Asset Optimization**: Image compression and format optimization
5. **Caching**: Long-term caching for static assets

### Runtime Optimizations

1. **Gzip Compression**: Text-based asset compression
2. **Brotli Compression**: Advanced compression for modern browsers
3. **HTTP/2**: Multiplexing and server push
4. **CDN Ready**: Static asset optimization for CDN deployment

### Bundle Analysis

```bash
# Analyze bundle size
npm run build:analyze

# Check for large dependencies
npx vite-bundle-analyzer dist
```

## Security Considerations

### Content Security Policy

The application includes a comprehensive CSP:

```html
Content-Security-Policy: default-src 'self'; 
  script-src 'self' 'unsafe-inline' 'unsafe-eval'; 
  style-src 'self' 'unsafe-inline'; 
  img-src 'self' data: blob:; 
  connect-src 'self' ws: wss:; 
  font-src 'self';
```

### Security Headers

- `X-Frame-Options`: Prevents clickjacking
- `X-XSS-Protection`: XSS protection
- `X-Content-Type-Options`: MIME type sniffing protection
- `Strict-Transport-Security`: HTTPS enforcement
- `Referrer-Policy`: Referrer information control

### Rate Limiting

- API endpoints: 10 requests/second
- Static assets: 30 requests/second
- Burst handling with nodelay

## Monitoring and Health Checks

### Health Check Endpoint

```bash
# Check application health
curl http://localhost:3000/health
```

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1
```

### Build Information

Build metadata is available at `/build-info.json`:

```json
{
  "version": "1.0.0",
  "buildTime": "2024-12-19T12:00:00.000Z",
  "gitHash": "abc1234",
  "environment": "production",
  "nodeVersion": "v18.17.0",
  "platform": "linux",
  "arch": "x64"
}
```

## Troubleshooting

### Common Issues

#### Build Failures

```bash
# Clear cache and rebuild
npm run clean
npm install
npm run build
```

#### Docker Build Issues

```bash
# Build without cache
docker build --no-cache -t health-dashboard:latest .

# Check build logs
docker build --progress=plain -t health-dashboard:latest .
```

#### Performance Issues

1. **Bundle Size**: Use `npm run build:analyze` to identify large dependencies
2. **Loading Time**: Check network tab for slow resources
3. **Memory Usage**: Monitor container memory consumption

#### Security Issues

1. **CSP Violations**: Check browser console for policy violations
2. **Mixed Content**: Ensure all resources use HTTPS
3. **CORS Issues**: Verify API endpoint configuration

### Debug Mode

```bash
# Enable debug logging
VITE_LOG_LEVEL=debug npm run dev

# Build with debug information
VITE_ENVIRONMENT=development npm run build
```

### Logs

- **Build Logs**: Check console output during build
- **Runtime Logs**: Monitor browser console and network tab
- **Docker Logs**: `docker logs ha-ingestor-dashboard`

## Deployment Checklist

- [ ] Environment variables configured
- [ ] Build process completed successfully
- [ ] Docker image built and tested
- [ ] Health checks passing
- [ ] Security headers configured
- [ ] Performance optimizations applied
- [ ] Monitoring setup complete
- [ ] Documentation updated

## Support

For deployment issues:

1. Check the troubleshooting section
2. Review build logs and error messages
3. Verify environment configuration
4. Test with development build first
5. Check Docker Compose service dependencies
