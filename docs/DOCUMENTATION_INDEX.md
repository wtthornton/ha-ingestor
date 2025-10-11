# 📚 Documentation Index - Home Assistant Ingestor

**Complete guide to all documentation in the HA Ingestor project**

---

## 🚀 Getting Started

Start here if you're new to the project:

1. **[Main README](../README.md)** - Project overview and quick start
2. **[Documentation README](README.md)** - Comprehensive project documentation
3. **[User Manual](USER_MANUAL.md)** - Complete user guide
4. **[Quick Reference](QUICK_REFERENCE_DOCKER.md)** - Docker quick reference

---

## 📖 Core Documentation

### System Overview
- **[Services Overview](SERVICES_OVERVIEW.md)** ⭐ NEW - Complete service reference
- **[Architecture](architecture.md)** - System architecture overview
- **[Architecture Documentation](architecture/)** - Detailed architecture docs (20 files)
- **[Requirements](REQUIREMENTS.md)** - Project requirements

### Deployment & Operations
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[Production Deployment](PRODUCTION_DEPLOYMENT.md)** - Production setup guide
- **[Docker Structure Guide](DOCKER_STRUCTURE_GUIDE.md)** - Docker configuration reference
- **[Docker Compose Services Reference](DOCKER_COMPOSE_SERVICES_REFERENCE.md)** - Service configurations
- **[Security Configuration](SECURITY_CONFIGURATION.md)** - Security best practices
- **[GitHub Secrets Setup](GITHUB_SECRETS_SETUP.md)** - CI/CD secrets configuration

### API & Integration
- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference
- **[API Endpoints Reference](API_ENDPOINTS_REFERENCE.md)** - Endpoint details
- **[CLI Reference](CLI_REFERENCE.md)** - Command-line tools
- **[WebSocket Call Tree](HA_WEBSOCKET_CALL_TREE.md)** - WebSocket flow diagram

### Troubleshooting & Support
- **[Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions
- **[WebSocket Troubleshooting](WEBSOCKET_TROUBLESHOOTING.md)** - WebSocket-specific issues
- **[Weather API Fix Guide](WEATHER_API_FIX_GUIDE.md)** - Weather API troubleshooting
- **[Smoke Tests](SMOKE_TESTS.md)** - System testing guide

---

## 🆕 Data Enrichment Enhancement (October 2025)

New documentation for the data enrichment platform:

### Product Documentation
- **[Data Enrichment PRD](DATA_ENRICHMENT_PRD.md)** ⭐ - Product requirements document
- **[Data Enrichment Architecture](DATA_ENRICHMENT_ARCHITECTURE.md)** ⭐ - Technical architecture
- **[Data Enrichment Deployment Guide](DATA_ENRICHMENT_DEPLOYMENT_GUIDE.md)** ⭐ - Deployment instructions
- **[Data Sources and Structures](DATA_SOURCES_AND_STRUCTURES_ENHANCEMENT.md)** ⭐ - Data models
- **[Data Backend Implementation](DATA_BACKEND_IMPLEMENTATION_GUIDE.md)** ⭐ - Implementation guide
- **[Data Enhancement Quick Reference](DATA_ENHANCEMENT_QUICK_REFERENCE.md)** ⭐ - Quick reference

### Project Status & Analysis
- **[Implementation Status](IMPLEMENTATION_STATUS.md)** ⭐ - Current implementation status
- **[Implementation Complete Summary](IMPLEMENTATION_COMPLETE_SUMMARY.md)** ⭐ - Completion report
- **[Top 10 Improvements Analysis](TOP_10_IMPROVEMENTS_ANALYSIS.md)** ⭐ - Impact analysis
- **[Improvements Executive Summary](IMPROVEMENTS_EXECUTIVE_SUMMARY.md)** ⭐ - Executive summary
- **[Improvements Visual Comparison](IMPROVEMENTS_VISUAL_COMPARISON.md)** ⭐ - Before/after comparison
- **[Device Recommendation Engine](DEVICE_RECOMMENDATION_ENGINE.md)** ⭐ - AI recommendation system

### New Services (October 2025)
1. **Carbon Intensity Service** - Carbon footprint data (Port 8010)
2. **Electricity Pricing Service** - Real-time pricing (Port 8011)
3. **Air Quality Service** - Air quality monitoring (Port 8012)
4. **Calendar Service** - Calendar integration (Port 8013)
5. **Smart Meter Service** - Energy consumption (Port 8014)

### Enhanced Features
- **Tiered Storage** - Hot/warm/cold retention with downsampling
- **Materialized Views** - Fast query performance
- **S3 Archival** - S3/Glacier integration
- **Storage Analytics** - Comprehensive monitoring

---

## 📋 Project Documentation

### Product & Planning
- **[PRD](prd.md)** - Product Requirements Document (sharded to `prd/`)
- **[PRD Shards](prd/)** - Individual PRD sections (18 files)
- **[Stories](stories/)** - User stories and epics (56 files)

### Quality Assurance
- **[QA Gates](qa/gates/)** - Quality gates (27 files)
- **[QA Assessments](qa/assessments/)** - Quality assessments (19 files)

### Knowledge Base
- **[Context7 Integration](CONTEXT7_INTEGRATION.md)** - Context7 documentation cache
- **[Knowledge Base](kb/)** - Cached documentation (5 files)

---

## 🗄️ Archive

Historical documentation moved to archive:

- **[Archive](archive/)** - Historical documentation
  - **[Planning](archive/planning/)** - Historical planning docs (11 files)
  - **[Summaries](archive/summaries/)** - Historical summaries (20 files)
  - **[Deployment Status (Jan 2025)](archive/DEPLOYMENT_STATUS_JANUARY_2025.md)**
  - **[Recent Fixes (Jan 2025)](archive/RECENT_FIXES_JANUARY_2025.md)**
  - **[Future Enhancements](archive/FUTURE_ENHANCEMENTS.md)**

---

## 🔧 Technical Documentation

### Development
- **[Development Environment Setup](development-environment-setup.md)** - Dev setup guide
- **[Architecture Detailed](architecture/)** - Complete architecture documentation
  - Introduction, Key Concepts, Tech Stack
  - Core Workflows, Data Models, Database Schema
  - Deployment Architecture, Source Tree
  - Testing Strategy, Error Handling
  - Monitoring & Observability
  - Performance & Security Standards
  - API Guidelines, Configuration Management
  - Development Workflow, Coding Standards

### Nabu Casa Integration
- **[Nabu Casa Fallback Guide](NABU_CASA_FALLBACK_GUIDE.md)** - Cloud fallback setup

---

## 📊 Status & Reporting

### Current Status
- **[Final Project Status](FINAL_PROJECT_STATUS.md)** - Overall project status
- **[Implementation Status](IMPLEMENTATION_STATUS.md)** ⭐ - Latest implementation status
- **[Documentation Updates](DOCUMENTATION_UPDATES_OCTOBER_2025.md)** - Recent doc updates
- **[Documentation Deduplication Report](DOCUMENTATION_DEDUPLICATION_REPORT.md)** - Cleanup report

---

## 🎯 Quick Access by Role

### For Users
1. [User Manual](USER_MANUAL.md) - How to use the system
2. [Services Overview](SERVICES_OVERVIEW.md) - What services are available
3. [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) - Fix common issues
4. [API Documentation](API_DOCUMENTATION.md) - API reference

### For Developers
1. [Architecture](architecture.md) - System design
2. [Development Environment Setup](development-environment-setup.md) - Dev setup
3. [Docker Structure Guide](DOCKER_STRUCTURE_GUIDE.md) - Docker configuration
4. [API Guidelines](architecture/api-guidelines.md) - API standards
5. [Coding Standards](architecture/coding-standards.md) - Code quality

### For DevOps
1. [Deployment Guide](DEPLOYMENT_GUIDE.md) - Deploy the system
2. [Production Deployment](PRODUCTION_DEPLOYMENT.md) - Production setup
3. [Security Configuration](SECURITY_CONFIGURATION.md) - Security setup
4. [Docker Compose Services Reference](DOCKER_COMPOSE_SERVICES_REFERENCE.md) - Service configs
5. [Monitoring and Observability](architecture/monitoring-and-observability.md) - Monitoring

### For Product Managers
1. [PRD](prd.md) - Product requirements
2. [Stories](stories/) - User stories and epics
3. [Final Project Status](FINAL_PROJECT_STATUS.md) - Project status
4. [Top 10 Improvements Analysis](TOP_10_IMPROVEMENTS_ANALYSIS.md) - Impact analysis
5. [Implementation Complete Summary](IMPLEMENTATION_COMPLETE_SUMMARY.md) - Completion report

---

## 📈 Documentation Statistics

### Total Documentation
- **Core Documentation:** 40+ files
- **Architecture Documentation:** 20 files
- **Data Enrichment Documentation:** 12 files (NEW)
- **User Stories:** 56 files
- **QA Documentation:** 46 files
- **Knowledge Base:** 5 files
- **Archive:** 31+ files

### Recently Updated (October 2025)
- Main README.md
- docs/README.md
- Architecture documentation
- API documentation
- Deployment guides
- User manual
- Troubleshooting guide
- Quick reference guides

### Recently Added (October 2025)
- Services Overview (NEW)
- Data Enrichment PRD
- Data Enrichment Architecture
- Data Enrichment Deployment Guide
- Implementation Status
- Implementation Complete Summary
- Top 10 Improvements Analysis
- Device Recommendation Engine
- Multiple data enhancement guides

---

## 🔍 Search & Navigation Tips

### Finding Information
1. **By Service:** See [Services Overview](SERVICES_OVERVIEW.md)
2. **By Topic:** Use this index or search documentation
3. **By Problem:** Check [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
4. **By API:** See [API Documentation](API_DOCUMENTATION.md)

### Key File Naming Conventions
- `*_GUIDE.md` - Step-by-step guides
- `*_REFERENCE.md` - Reference documentation
- `*_STATUS.md` - Status reports
- `*_SUMMARY.md` - Executive summaries
- `*_ANALYSIS.md` - Detailed analysis

---

## 📝 Contributing to Documentation

When adding or updating documentation:
1. Follow [Documentation Standards](.cursor/rules/documentation-standards.mdc)
2. Update this index if adding new files
3. Use consistent formatting and structure
4. Include examples where appropriate
5. Keep documentation synchronized with code

---

## 📞 Getting Help

### Documentation Issues
- File an issue on GitHub
- Check [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
- Review [User Manual](USER_MANUAL.md)

### Need More Info?
- See [Architecture Documentation](architecture/)
- Check [API Documentation](API_DOCUMENTATION.md)
- Review service-specific READMEs

---

**Last Updated:** October 2025  
**Total Documentation Files:** 200+  
**Status:** Comprehensive and up-to-date

---

**⭐ Bookmark this page for easy access to all documentation!**

