# Sports API - Endpoint Documentation

Simple REST API for NFL and NHL sports data.

## Base URL
```
http://localhost:8015
```

---

## NFL Endpoints

### GET /api/nfl/scores
Get NFL scores (live or historical).

**Query Parameters:**
- `date` (optional): Date in YYYY-MM-DD format. Omit for live scores.

**Example:**
```bash
# Live scores
curl http://localhost:8015/api/nfl/scores

# Historical scores
curl http://localhost:8015/api/nfl/scores?date=2025-10-11
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "game_id": "12345",
      "home_team": "Patriots",
      "away_team": "Chiefs",
      "home_score": 24,
      "away_score": 21,
      "status": "finished",
      "season": 2025,
      "week": 5
    }
  ],
  "metadata": {
    "source": "cache",
    "timestamp": "2025-10-11T18:30:00Z",
    "count": 1
  }
}
```

---

### GET /api/nfl/standings
Get NFL standings by season.

**Query Parameters:**
- `season` (optional): Season year (default: current year)

**Example:**
```bash
curl http://localhost:8015/api/nfl/standings?season=2025
```

---

### GET /api/nfl/fixtures
Get NFL game schedule.

**Query Parameters:**
- `season` (optional): Season year (default: current year)
- `week` (optional): Week number

**Example:**
```bash
# Full season
curl http://localhost:8015/api/nfl/fixtures?season=2025

# Specific week
curl http://localhost:8015/api/nfl/fixtures?season=2025&week=5
```

---

### GET /api/nfl/injuries
Get NFL injury reports.

**Query Parameters:**
- `team` (optional): Team name filter

**Example:**
```bash
# All teams
curl http://localhost:8015/api/nfl/injuries

# Specific team
curl http://localhost:8015/api/nfl/injuries?team=Patriots
```

---

## NHL Endpoints

### GET /api/nhl/scores
Get NHL scores (live or historical).

**Query Parameters:**
- `date` (optional): Date in YYYY-MM-DD format

**Example:**
```bash
curl http://localhost:8015/api/nhl/scores
```

---

### GET /api/nhl/standings
Get NHL standings by season.

**Query Parameters:**
- `season` (optional): Season year (default: current year)

---

### GET /api/nhl/fixtures
Get NHL game schedule.

**Query Parameters:**
- `season` (optional): Season year (default: current year)

---

## Admin Endpoints

### GET /api/sports/stats
Get service statistics.

**Example:**
```bash
curl http://localhost:8015/api/sports/stats
```

**Response:**
```json
{
  "status": "success",
  "stats": {
    "cache": {
      "hits": 45,
      "misses": 15,
      "hit_rate": 0.75,
      "cache_size": 12
    },
    "rate_limiter": {
      "total_requests": 60,
      "total_waits": 20,
      "rate_per_second": 1.0
    },
    "influxdb": {
      "total_points_written": 100,
      "success_rate": 0.98
    }
  }
}
```

---

### POST /api/sports/cache/clear
Clear all cached data.

**Example:**
```bash
curl -X POST http://localhost:8015/api/sports/cache/clear
```

---

### GET /health
Service health check.

**Example:**
```bash
curl http://localhost:8015/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "sports-api",
  "version": "1.0.0",
  "components": {
    "nfl_client": "healthy",
    "nhl_client": "healthy",
    "cache": "healthy",
    "rate_limiter": "healthy",
    "influxdb": "healthy"
  },
  "endpoints": {
    "nfl": ["/api/nfl/scores", "/api/nfl/standings", "/api/nfl/fixtures", "/api/nfl/injuries"],
    "nhl": ["/api/nfl/scores", "/api/nhl/standings", "/api/nhl/fixtures"],
    "admin": ["/api/sports/stats", "/api/sports/cache/clear"]
  }
}
```

---

## Performance Features

### Caching
- **Live scores:** 15 second TTL
- **Recent scores:** 5 minute TTL
- **Fixtures:** 1 hour TTL
- **Standings:** 1 hour TTL
- **Injuries:** 30 minute TTL

### Rate Limiting
- **Rate:** 1 request/second (configurable)
- **Burst:** 5 requests
- **Algorithm:** Token bucket

### InfluxDB
- **Batch size:** 100 points
- **Flush interval:** 10 seconds
- **Retention:** 2-5 years

---

## Error Responses

### 503 Service Unavailable
```json
{
  "status": "error",
  "error": "NFL client not initialized"
}
```

### 500 Internal Server Error
```json
{
  "status": "error",
  "error": "API Error message"
}
```

---

**Simple, clean, and production-ready!** 🎯

