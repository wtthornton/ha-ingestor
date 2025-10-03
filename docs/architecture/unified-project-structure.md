# Unified Project Structure

```
ha-ingestor/
├── .github/                           # CI/CD workflows
│   └── workflows/
│       ├── ci.yml                     # Continuous integration
│       └── deploy.yml                 # Deployment workflow
├── services/                          # Backend services
│   ├── websocket-ingestion/           # WebSocket client service
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                # Service entry point
│   │   │   ├── websocket_client.py    # HA WebSocket client
│   │   │   ├── event_processor.py     # Event processing logic
│   │   │   └── health_check.py        # Health monitoring
│   │   ├── tests/
│   │   │   ├── test_websocket_client.py
│   │   │   └── test_event_processor.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── enrichment-pipeline/           # Data enrichment service
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── weather_service.py     # Weather API integration
│   │   │   ├── data_normalizer.py     # Data normalization
│   │   │   └── influxdb_client.py     # Database operations
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── admin-api/                     # Admin REST API
│       ├── src/
│       │   ├── __init__.py
│       │   ├── main.py                # FastAPI application
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   ├── health.py          # Health endpoints
│       │   │   ├── stats.py           # Statistics endpoints
│       │   │   ├── events.py          # Events endpoints
│       │   │   └── config.py          # Configuration endpoints
│       │   ├── models/                # Data models
│       │   │   ├── __init__.py
│       │   │   ├── events.py
│       │   │   ├── health.py
│       │   │   └── config.py
│       │   └── services/              # Business logic
│       │       ├── __init__.py
│       │       ├── health_service.py
│       │       └── config_service.py
│       ├── tests/
│       ├── Dockerfile
│       └── requirements.txt
├── frontend/                          # Admin dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── HealthDashboard.tsx    # System health display
│   │   │   ├── EventList.tsx          # Recent events list
│   │   │   ├── StatsDisplay.tsx       # Statistics display
│   │   │   └── ConfigForm.tsx         # Configuration form
│   │   ├── services/
│   │   │   ├── api.ts                 # API client
│   │   │   └── types.ts               # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── tests/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── shared/                            # Shared code and types
│   ├── types/
│   │   ├── events.ts                  # Event data types
│   │   ├── health.ts                  # Health data types
│   │   └── config.ts                  # Configuration types
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py                 # Shared logging utilities
│   │   └── validation.py              # Data validation
│   └── constants/
│       ├── __init__.py
│       └── schemas.py                 # Database schemas
├── infrastructure/                    # Deployment configuration
│   ├── docker-compose.yml             # Main orchestration
│   ├── docker-compose.dev.yml         # Development environment
│   ├── docker-compose.prod.yml        # Production environment
│   ├── .env.example                   # Environment template
│   └── influxdb/
│       ├── init-scripts/
│       │   ├── setup-database.sql     # Database initialization
│       │   └── create-retention.sql   # Retention policies
│       └── config/
│           └── influxdb.conf          # InfluxDB configuration
├── scripts/                           # Utility scripts
│   ├── setup.sh                       # Initial setup script
│   ├── backup.sh                      # Data backup script
│   ├── restore.sh                     # Data restore script
│   └── health-check.sh                # System health check
├── docs/                              # Documentation
│   ├── prd.md                         # Product requirements
│   ├── architecture.md                # This architecture document
│   ├── setup.md                       # Setup instructions
│   ├── api.md                         # API documentation
│   └── troubleshooting.md             # Troubleshooting guide
├── tests/                             # Integration tests
│   ├── __init__.py
│   ├── test_integration.py            # End-to-end tests
│   ├── test_data_flow.py              # Data flow tests
│   └── fixtures/                      # Test data
├── .env.example                       # Environment variables template
├── .gitignore
├── docker-compose.yml                 # Main compose file
├── README.md
└── requirements.txt                   # Python dependencies
```
