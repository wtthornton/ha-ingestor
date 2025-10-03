# Tech Stack

This is the DEFINITIVE technology selection for the entire project. Based on the PRD requirements and architectural analysis, here are the technology choices:

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| Backend Language | Python | 3.11 | WebSocket client and data processing | Simple, proven async support |
| Backend Framework | aiohttp | 3.9+ | WebSocket client + REST API | Native async WebSocket + simple HTTP API |
| Frontend Language | TypeScript | 5.0+ | Admin web interface | Type safety for shared data models |
| Frontend Framework | React | 18+ | Admin dashboard | Simple, proven UI framework |
| UI Component Library | None (Custom CSS) | - | Simple admin interface | Keep it minimal, no external dependencies |
| State Management | React Context | - | Frontend state | Built-in React state management |
| Database | InfluxDB | 2.7 | Time-series data storage | Purpose-built for this use case |
| File Storage | Local Docker Volumes | - | Persistent data storage | Simple local storage |
| Authentication | Long-lived Access Tokens | - | Home Assistant authentication | HA's standard auth method |
| API Style | WebSocket + REST | - | Real-time + admin API | WebSocket for HA, REST for admin interface |
| Frontend Testing | Jest + React Testing Library | 29+ | Frontend component testing | Standard React testing |
| Backend Testing | pytest | 7.4+ | Backend service testing | Simple, comprehensive testing |
| E2E Testing | pytest + requests | - | API integration testing | Test admin API endpoints |
| Build Tool | Docker | 24+ | Containerization | Standard deployment |
| Bundler | Vite | 5.0+ | Frontend build tool | Fast, simple build tool |
| Orchestration | Docker Compose | 2.20+ | Service orchestration | Simple orchestration |
| CI/CD | GitHub Actions | - | Automated testing | Free CI/CD |
| Monitoring | Python logging | - | Application logging | Built-in logging |
| Logging | Python logging | - | Application logging | Standard logging |
| CSS Framework | Custom CSS | - | Simple styling | Minimal styling, no frameworks |
