# ML Service

**Machine Learning Service - Clustering and Anomaly Detection**

Containerized ML service providing K-Means clustering, anomaly detection, and pattern grouping using scikit-learn algorithms.

---

## 📊 Overview

**Port:** 8025
**Technology:** Python 3.11, scikit-learn, FastAPI
**Container:** `homeiq-ml-service`
**Phase:** Phase 1 AI Containerization (October 2025)

### Purpose

Provide machine learning capabilities for:
- K-Means clustering of device usage patterns
- Anomaly detection in sensor data
- Pattern grouping and segmentation
- Statistical analysis

---

## 🎯 Features

### Clustering Algorithms

**K-Means Clustering:**
- Time-based pattern clustering
- Device usage grouping
- Optimal cluster count (elbow method)
- Silhouette scoring

**DBSCAN:**
- Density-based clustering
- Outlier detection
- Variable cluster sizes

### Anomaly Detection

**Isolation Forest:**
- Unsupervised anomaly detection
- Multi-dimensional data support
- Contamination parameter tuning

**Statistical Methods:**
- Z-score based detection
- IQR (Interquartile Range)
- Moving average deviation

### Pattern Analysis

- Time-series clustering
- Event sequence analysis
- Feature extraction
- Dimensionality reduction (PCA)

---

## 🔌 API Endpoints

### Clustering

```bash
POST /cluster
Content-Type: application/json

{
  "data": [[1, 2], [1.5, 1.8], [5, 8], [8, 8], [1, 0.6]],
  "algorithm": "kmeans",
  "n_clusters": 2
}

Response:
{
  "clusters": [0, 0, 1, 1, 0],
  "centroids": [[1.17, 1.47], [6.5, 8.0]],
  "silhouette_score": 0.79,
  "inertia": 12.34,
  "algorithm": "kmeans"
}
```

### Anomaly Detection

```bash
POST /detect-anomalies
Content-Type: application/json

{
  "data": [[1, 2], [1.5, 1.8], [100, 200], [1, 0.6]],
  "method": "isolation_forest",
  "contamination": 0.1
}

Response:
{
  "anomalies": [false, false, true, false],
  "anomaly_indices": [2],
  "anomaly_scores": [-0.2, -0.18, 0.95, -0.22],
  "method": "isolation_forest"
}
```

### Pattern Grouping

```bash
POST /group-patterns
Content-Type: application/json

{
  "events": [
    {"hour": 7, "device": "light.bedroom"},
    {"hour": 7, "device": "light.kitchen"},
    {"hour": 22, "device": "light.bedroom"}
  ],
  "group_by": "hour"
}

Response:
{
  "groups": {
    "morning": [...],
    "evening": [...]
  },
  "group_counts": {
    "morning": 2,
    "evening": 1
  }
}
```

### Health

```bash
GET /health

Response:
{
  "status": "healthy",
  "algorithms": ["kmeans", "dbscan", "isolation_forest"],
  "scikit_learn_version": "1.3.0"
}
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Service Configuration
ML_SERVICE_PORT=8025
LOG_LEVEL=INFO

# Algorithm Settings
KMEANS_MAX_ITER=300
KMEANS_N_INIT=10
DBSCAN_EPS=0.5
DBSCAN_MIN_SAMPLES=5
ISOLATION_FOREST_N_ESTIMATORS=100

# Performance
MAX_DATA_POINTS=10000
PARALLEL_JOBS=-1  # Use all CPU cores
```

---

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
# Start service
docker-compose up ml-service

# Check health
curl http://localhost:8025/health
```

### Standalone Docker

```bash
# Build
docker build -t homeiq-ml -f services/ml-service/Dockerfile .

# Run
docker run -p 8025:8025 homeiq-ml
```

### Local Development

```bash
cd services/ml-service

# Install dependencies
pip install -r requirements.txt

# Run
python src/main.py
```

---

## 📊 Performance

### Processing Speed

| Operation | Data Points | Time |
|-----------|-------------|------|
| K-Means (2 clusters) | 1,000 | ~50ms |
| K-Means (5 clusters) | 1,000 | ~100ms |
| Isolation Forest | 1,000 | ~80ms |
| DBSCAN | 1,000 | ~60ms |

### Resource Usage
- Memory: 128-256MB baseline
- CPU: Scales with data points
- Startup: 5-10 seconds

---

## 🏗️ Architecture

### Service Structure

```
ML Service (8025)
├── Clustering Module
│   ├── K-Means
│   ├── DBSCAN
│   └── Hierarchical
├── Anomaly Detection
│   ├── Isolation Forest
│   ├── One-Class SVM
│   └── Statistical Methods
└── Pattern Analysis
    ├── Feature Extraction
    ├── Dimensionality Reduction
    └── Time-series Analysis
```

### Data Flow

```
Input Data (Events, Sensor Readings)
    ↓
Preprocessing (Normalization, Scaling)
    ↓
Algorithm Selection
    ├→ Clustering
    ├→ Anomaly Detection
    └→ Pattern Grouping
    ↓
Results + Metrics
```

---

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Test specific algorithm
pytest tests/test_clustering.py

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Manual Testing

```bash
# Test clustering
curl -X POST http://localhost:8025/cluster \
  -H "Content-Type: application/json" \
  -d '{
    "data": [[1,2],[2,2],[8,7],[8,8]],
    "algorithm": "kmeans",
    "n_clusters": 2
  }'

# Test anomaly detection
curl -X POST http://localhost:8025/detect-anomalies \
  -H "Content-Type: application/json" \
  -d '{
    "data": [[1,1],[2,2],[100,100]],
    "method": "isolation_forest"
  }'
```

---

## 🔍 Troubleshooting

### High Memory Usage

**Cause:** Large dataset clustering

**Solutions:**
```bash
# Reduce max data points
MAX_DATA_POINTS=5000

# Use mini-batch K-Means for large datasets
# (Implemented in code)
```

### Slow Clustering

**Optimization:**
```python
# Reduce iterations
KMEANS_MAX_ITER=100

# Reduce n_init
KMEANS_N_INIT=3

# Use parallel processing
PARALLEL_JOBS=-1  # All cores
```

### Poor Clustering Results

**Tuning:**
```bash
# Adjust cluster count
# Use elbow method to find optimal k

# Normalize data before clustering
# Scale features to same range
```

---

## 📚 Algorithms Reference

### K-Means Clustering

**Best for:**
- Spherical clusters
- Known cluster count
- Fast clustering

**Parameters:**
- `n_clusters`: Number of clusters
- `max_iter`: Maximum iterations
- `n_init`: Number of initializations

### DBSCAN

**Best for:**
- Arbitrary shaped clusters
- Unknown cluster count
- Noise detection

**Parameters:**
- `eps`: Maximum distance between points
- `min_samples`: Minimum cluster size

### Isolation Forest

**Best for:**
- Unsupervised anomaly detection
- High-dimensional data
- Fast processing

**Parameters:**
- `n_estimators`: Number of trees
- `contamination`: Expected anomaly ratio

---

## 📚 Related Documentation

- [AI Core Service](../ai-core-service/README.md) - AI orchestration
- [OpenVINO Service](../openvino-service/README.md) - Deep learning
- [Phase 1 AI Models](../ai-automation-service/README-PHASE1-MODELS.md)
- [scikit-learn Documentation](https://scikit-learn.org/)

---

## 🤝 Integration

### Used By
- AI Core Service (8018)
- Automation Miner (8029)
- Device Intelligence Service (8028)

### Data Sources
- InfluxDB (via AI Core)
- Data API (8006)

---

## 🔧 Advanced Usage

### Custom Clustering

```python
from sklearn.cluster import KMeans

# Configure custom algorithm
kmeans = KMeans(
    n_clusters=3,
    init='k-means++',
    max_iter=300,
    n_init=10,
    random_state=42
)

# Fit and predict
labels = kmeans.fit_predict(data)
```

### Feature Engineering

```python
# Time-based features
features = extract_features(events)
# [hour_of_day, day_of_week, device_type, duration]

# Dimensionality reduction
from sklearn.decomposition import PCA
pca = PCA(n_components=2)
reduced = pca.fit_transform(features)
```

---

**Version:** 1.0.0 (Phase 1)
**Status:** ✅ Production Ready
**Last Updated:** October 25, 2025
**scikit-learn Version:** 1.3.0
