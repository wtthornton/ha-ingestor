#!/bin/bash

# Setup ELK Stack for HA Ingestor
# This script sets up the ELK stack for centralized log aggregation

set -e

echo "Setting up ELK Stack for HA Ingestor..."

# Create log directory
echo "Creating log directory..."
sudo mkdir -p /var/log/homeiq
sudo chmod 755 /var/log/homeiq

# Create ELK stack directory structure
echo "Creating ELK stack directory structure..."
mkdir -p infrastructure/elk-stack/{elasticsearch,logstash/{pipeline,config},kibana,filebeat}

# Set up Elasticsearch index lifecycle management policy
echo "Setting up Elasticsearch ILM policy..."
curl -X PUT "localhost:9200/_ilm/policy/homeiq-policy" \
  -H "Content-Type: application/json" \
  -d @infrastructure/elk-stack/elasticsearch/ilm-policy.json

# Create index template
echo "Creating index template..."
curl -X PUT "localhost:9200/_index_template/homeiq-logs" \
  -H "Content-Type: application/json" \
  -d '{
    "index_patterns": ["homeiq-logs-*"],
    "template": {
      "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "index.lifecycle.name": "homeiq-policy",
        "index.lifecycle.rollover_alias": "homeiq-logs"
      },
      "mappings": {
        "properties": {
          "@timestamp": { "type": "date" },
          "timestamp": { "type": "date" },
          "level": { "type": "keyword" },
          "log_level": { "type": "keyword" },
          "service": { "type": "keyword" },
          "service_name": { "type": "keyword" },
          "message": { "type": "text" },
          "correlation_id": { "type": "keyword" },
          "operation": { "type": "keyword" },
          "event_type": { "type": "keyword" },
          "entity_id": { "type": "keyword" },
          "domain": { "type": "keyword" },
          "environment": { "type": "keyword" },
          "log_type": { "type": "keyword" }
        }
      }
    }
  }'

# Start ELK stack services
echo "Starting ELK stack services..."
docker-compose -f infrastructure/elk-stack/docker-compose.elk.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Check service health
echo "Checking service health..."
curl -f http://localhost:9200/_cluster/health || echo "Elasticsearch not ready"
curl -f http://localhost:5601/api/status || echo "Kibana not ready"

# Create Kibana index pattern
echo "Creating Kibana index pattern..."
curl -X POST "localhost:5601/api/saved_objects/index-pattern/homeiq-logs" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d '{
    "attributes": {
      "title": "homeiq-logs-*",
      "timeFieldName": "@timestamp"
    }
  }'

echo "ELK Stack setup completed!"
echo "Access Kibana at: http://localhost:5601"
echo "Access Elasticsearch at: http://localhost:9200"
echo "Logs are being collected from: /var/log/homeiq/"
