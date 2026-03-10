# Metrics and Monitoring Guide

This guide explains the metrics collection, monitoring, and alerting system implemented in the Document Analyzer.

## Overview

The system provides comprehensive monitoring through:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Custom Metrics**: Application-specific metrics for document processing
- **Alerting**: Performance and error monitoring

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │───▶│   Prometheus     │───▶│    Grafana      │
│                 │    │                  │    │                 │
│ • Custom Metrics│    │ • Time Series DB │    │ • Dashboards    │
│ • HTTP Metrics  │    │ • Alert Manager  │    │ • Alerts        │
│ • System Metrics│    │ • Scraping       │    │ • Export        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Metrics Categories

### 1. Document Processing Metrics

#### `document_processing_total`
- **Type**: Counter
- **Description**: Total number of documents processed
- **Labels**: `document_type`, `status`, `user_id`
- **Use Case**: Track processing volume and success rates

#### `document_processing_duration_seconds`
- **Type**: Histogram
- **Description**: Time taken to process documents
- **Labels**: `document_type`, `status`
- **Use Case**: Performance monitoring and SLA tracking

#### `document_size_bytes`
- **Type**: Histogram
- **Description**: Size of processed documents
- **Labels**: `document_type`
- **Use Case**: Resource planning and optimization

### 2. PII Detection Metrics

#### `pii_detection_total`
- **Type**: Counter
- **Description**: Total number of PII entities detected
- **Labels**: `entity_type`, `document_type`
- **Use Case**: Privacy compliance monitoring

#### `pii_detection_rate`
- **Type**: Gauge
- **Description**: Rate of PII detection per document
- **Labels**: `document_type`
- **Use Case**: PII detection effectiveness

### 3. LLM Extraction Metrics

#### `llm_extraction_confidence`
- **Type**: Histogram
- **Description**: Confidence scores for LLM field extraction
- **Labels**: `field_name`, `document_type`
- **Use Case**: AI model performance evaluation

#### `llm_extraction_total`
- **Type**: Counter
- **Description**: Total number of fields extracted by LLM
- **Labels**: `field_name`, `document_type`, `status`
- **Use Case**: Extraction success rates

### 4. Error Metrics

#### `error_total`
- **Type**: Counter
- **Description**: Total number of errors by category
- **Labels**: `error_type`, `component`, `document_type`
- **Use Case**: Error tracking and debugging

### 5. System Metrics

#### `active_connections`
- **Type**: Gauge
- **Description**: Number of active connections
- **Labels**: `connection_type`
- **Use Case**: Resource utilization monitoring

#### `queue_size`
- **Type**: Gauge
- **Description**: Current queue size for processing
- **Labels**: `queue_name`
- **Use Case**: Load balancing and capacity planning

## Grafana Dashboards

### 1. Document Processing Dashboard

#### Key Panels
- **Processing Rate**: Documents processed per minute
- **Processing Duration**: P50, P95, P99 percentiles
- **Success Rate**: Percentage of successful processing
- **Error Rate**: Failed processing attempts

#### Configuration
- **Refresh Rate**: 5 seconds
- **Time Range**: Last 1 hour (default)
- **Alert Thresholds**: Configurable

### 2. PII Detection Dashboard

#### Key Panels
- **PII Detection Rate**: Entities detected per minute
- **PII by Type**: Breakdown by entity type
- **PII by Document Type**: Detection rates by document category
- **Anonymization Success**: PII anonymization effectiveness

### 3. System Health Dashboard

#### Key Panels
- **Active Connections**: Current system load
- **Queue Size**: Processing queue depth
- **Memory Usage**: Application memory consumption
- **CPU Usage**: System CPU utilization

### 4. Performance Dashboard

#### Key Panels
- **Response Times**: API endpoint performance
- **Throughput**: Requests per second
- **Error Breakdown**: Error types and frequencies
- **Resource Utilization**: System resource usage

## Alerting Configuration

### 1. Performance Alerts

#### High Processing Time
```yaml
alert: HighProcessingTime
expr: histogram_quantile(0.95, rate(document_processing_duration_seconds_bucket[5m])) > 30
for: 5m
labels:
  severity: warning
annotations:
  summary: "High document processing time detected"
  description: "95th percentile processing time is {{ $value }} seconds"
```

#### Low Success Rate
```yaml
alert: LowSuccessRate
expr: (rate(document_processing_total{status="completed"}[5m]) / rate(document_processing_total[5m])) < 0.95
for: 2m
labels:
  severity: critical
annotations:
  summary: "Low document processing success rate"
  description: "Success rate is {{ $value | humanizePercentage }}"
```

### 2. Error Alerts

#### High Error Rate
```yaml
alert: HighErrorRate
expr: rate(error_total[5m]) > 0.1
for: 1m
labels:
  severity: critical
annotations:
  summary: "High error rate detected"
  description: "Error rate is {{ $value }} errors per second"
```

#### Specific Error Types
```yaml
alert: PIIProcessingError
expr: rate(error_total{error_type="pii_processing"}[5m]) > 0
for: 30s
labels:
  severity: warning
annotations:
  summary: "PII processing errors detected"
  description: "PII processing errors: {{ $value }}"
```

### 3. Resource Alerts

#### High Memory Usage
```yaml
alert: HighMemoryUsage
expr: (process_resident_memory_bytes / 1024 / 1024) > 1000
for: 5m
labels:
  severity: warning
annotations:
  summary: "High memory usage detected"
  description: "Memory usage is {{ $value }} MB"
```

#### Queue Backlog
```yaml
alert: QueueBacklog
expr: queue_size{queue_name="document_processing"} > 100
for: 2m
labels:
  severity: warning
annotations:
  summary: "Document processing queue backlog"
  description: "Queue size is {{ $value }}"
```

## Monitoring Best Practices

### 1. Metric Collection

#### Label Management
- Use consistent label names across metrics
- Limit label cardinality to avoid performance issues
- Use meaningful label values

#### Metric Naming
- Follow Prometheus naming conventions
- Use descriptive metric names
- Group related metrics with common prefixes

### 2. Dashboard Design

#### Panel Organization
- Group related metrics together
- Use consistent time ranges
- Include appropriate legends and units

#### Visualization Types
- Use gauges for current values
- Use graphs for time-series data
- Use tables for detailed breakdowns

### 3. Alert Configuration

#### Threshold Setting
- Base thresholds on historical data
- Consider business requirements
- Test alert conditions

#### Alert Fatigue Prevention
- Use appropriate alert frequencies
- Group related alerts
- Provide clear resolution steps

## Troubleshooting

### 1. Missing Metrics

#### Check Prometheus Configuration
```bash
# Verify Prometheus is scraping the application
curl http://localhost:9090/targets

# Check if metrics endpoint is accessible
curl http://localhost:8000/metrics
```

#### Verify Application Metrics
```bash
# Check if custom metrics are being collected
curl http://localhost:8000/metrics | grep document_processing
```

### 2. Dashboard Issues

#### Check Data Source
- Verify Grafana data source configuration
- Ensure Prometheus is accessible
- Check time range settings

#### Panel Configuration
- Verify metric queries
- Check label filters
- Validate visualization settings

### 3. Alert Problems

#### Check Alert Rules
```bash
# Verify alert rules are loaded
curl http://localhost:9090/api/v1/rules

# Check alert status
curl http://localhost:9090/api/v1/alerts
```

#### Alert Manager Configuration
- Verify Alert Manager is running
- Check notification channels
- Review alert routing rules

## Performance Optimization

### 1. Metric Collection

#### Reduce Cardinality
- Limit label combinations
- Use appropriate bucket sizes for histograms
- Avoid high-cardinality labels

#### Sampling
- Use sampling for high-frequency metrics
- Implement metric aggregation
- Consider metric retention policies

### 2. Dashboard Performance

#### Query Optimization
- Use appropriate time ranges
- Limit data points
- Use recording rules for complex queries

#### Panel Configuration
- Use caching where appropriate
- Limit concurrent queries
- Optimize visualization settings

### 3. Alert Efficiency

#### Alert Grouping
- Group related alerts
- Use alert templates
- Implement alert suppression

#### Notification Optimization
- Use appropriate notification channels
- Implement escalation policies
- Consider alert fatigue

## Integration with External Systems

### 1. Log Aggregation

#### ELK Stack Integration
- Export metrics to Elasticsearch
- Create Kibana dashboards
- Set up log correlation

#### Splunk Integration
- Forward metrics to Splunk
- Create Splunk dashboards
- Implement alerting workflows

### 2. Monitoring Platforms

#### CloudWatch Integration
- Export metrics to AWS CloudWatch
- Create CloudWatch dashboards
- Set up CloudWatch alarms

#### Datadog Integration
- Forward metrics to Datadog
- Create Datadog dashboards
- Implement Datadog alerts

## Security Considerations

### 1. Metric Security

#### Access Control
- Secure metrics endpoints
- Implement authentication
- Use HTTPS for metric transmission

#### Sensitive Data
- Avoid exposing sensitive information in metrics
- Use appropriate label values
- Implement data masking

### 2. Alert Security

#### Notification Security
- Secure notification channels
- Use encrypted communication
- Implement access controls

#### Alert Content
- Avoid sensitive information in alerts
- Use appropriate alert descriptions
- Implement alert filtering

## Maintenance

### 1. Regular Tasks

#### Metric Review
- Review metric usage regularly
- Remove unused metrics
- Update metric definitions as needed

#### Dashboard Maintenance
- Update dashboard configurations
- Review panel effectiveness
- Clean up unused dashboards

#### Alert Review
- Review alert effectiveness
- Update alert thresholds
- Remove obsolete alerts

### 2. Performance Monitoring

#### System Health
- Monitor Prometheus performance
- Check Grafana performance
- Review alert manager performance

#### Resource Usage
- Monitor storage usage
- Check memory consumption
- Review network usage

This comprehensive monitoring system ensures the Document Analyzer operates reliably and provides valuable insights into system performance and document processing effectiveness.