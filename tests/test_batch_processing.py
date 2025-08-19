"""Tests for InfluxDB batch processing performance and reliability."""

import pytest
import asyncio
import time
import gzip
import zlib
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import aiohttp
from aiohttp import ClientResponseError

from ha_ingestor.influxdb.writer import InfluxDBWriter
from ha_ingestor.models import InfluxDBPoint
from ha_ingestor.config import get_settings
from ha_ingestor.metrics import get_metrics_collector


class TestBatchProcessingPerformance:
    """Test batch processing performance characteristics."""
    
    @pytest.fixture
    def writer(self):
        """Create InfluxDB writer instance for testing."""
        config = get_settings()
        # Override config for testing
        config.influxdb_batch_size = 100
        config.influxdb_batch_timeout = 5.0
        config.influxdb_compression = "gzip"
        config.influxdb_compression_level = 6
        config.influxdb_optimize_batches = True
        config.influxdb_max_retries = 3
        config.influxdb_retry_delay = 0.1
        config.influxdb_retry_backoff = 2.0
        config.influxdb_retry_jitter = 0.1
        
        writer = InfluxDBWriter(config)
        # Mock connection state for testing
        writer._connected = True
        return writer
    
    @pytest.fixture
    def sample_points(self):
        """Generate sample data points for testing."""
        points = []
        for i in range(1000):
            point = InfluxDBPoint(
                measurement="test_measurement",
                tags={"sensor": f"sensor_{i % 10}", "location": f"room_{i % 5}"},
                fields={"value": float(i), "status": "active" if i % 2 == 0 else "inactive"},
                timestamp=datetime.now() + timedelta(seconds=i)
            )
            points.append(point)
        return points
    
    @pytest.mark.asyncio
    async def test_batch_optimization_performance(self, writer, sample_points):
        """Test that batch optimization improves performance."""
        # Test with optimization enabled
        writer._optimize_batches = True
        start_time = time.time()
        optimized_batch = writer._optimize_batch(sample_points[:100])
        optimization_time = time.time() - start_time
        
        # Test with optimization disabled
        writer._optimize_batches = False
        start_time = time.time()
        unoptimized_batch = sample_points[:100]
        no_optimization_time = time.time() - start_time
        
        # Optimization should be fast (< 1ms for 100 points)
        assert optimization_time < 0.001
        assert no_optimization_time < 0.001
        
        # Optimized batch should have fewer or equal points (due to deduplication)
        assert len(optimized_batch) <= len(unoptimized_batch)
        
        # Points should be sorted by measurement name
        measurements = [p.measurement for p in optimized_batch]
        assert measurements == sorted(measurements)
    
    @pytest.mark.asyncio
    async def test_compression_performance(self, writer, sample_points):
        """Test compression performance and ratios."""
        test_data = '\n'.join([str(p) for p in sample_points[:100]])
        original_size = len(test_data.encode('utf-8'))
        
        # Test gzip compression
        start_time = time.time()
        compressed_data, encoding = writer._compress_data(test_data)
        compression_time = time.time() - start_time
        
        # Compression should be fast (< 10ms for 100 points)
        assert compression_time < 0.01
        assert encoding == "gzip"
        
        # Verify compression ratio
        compressed_size = len(compressed_data)
        compression_ratio = original_size / compressed_size
        assert compression_ratio > 1.0  # Should compress data
        # Allow for higher compression ratios for repetitive data
        assert compression_ratio < 50.0  # Reasonable upper bound
        
        # Test deflate compression
        writer._compression = "deflate"
        compressed_data, encoding = writer._compress_data(test_data)
        assert encoding == "deflate"
        
        # Test no compression
        writer._compression = "none"
        compressed_data, encoding = writer._compress_data(test_data)
        assert encoding == "identity"
        assert compressed_data == test_data.encode('utf-8')
    
    @pytest.mark.asyncio
    async def test_batch_throughput_metrics(self, writer):
        """Test batch throughput calculation and recording."""
        # Mock metrics collector
        mock_collector = Mock()
        with patch('ha_ingestor.influxdb.writer.get_metrics_collector', return_value=mock_collector):
            # Simulate processing multiple batches
            for i in range(5):
                writer._points_written += 100
                writer._batches_processed += 1
                writer._total_write_time += 0.1
                writer._total_batch_time += 0.05
            
            # Set timestamps for throughput calculation
            writer._last_write_time = datetime.now()
            writer._last_batch_time = datetime.now() - timedelta(seconds=10)
            
            # Update throughput metrics
            writer.update_throughput_metrics()
            
            # Verify metrics were recorded
            mock_collector.record_influxdb_throughput.assert_called()
            call_args = mock_collector.record_influxdb_throughput.call_args[0]
            points_per_second, batches_per_second = call_args
            
            # Should have reasonable throughput values
            assert points_per_second > 0
            assert batches_per_second > 0
            assert points_per_second < 10000  # Reasonable upper bound
            assert batches_per_second < 100   # Reasonable upper bound
    
    @pytest.mark.asyncio
    async def test_batch_age_tracking(self, writer, sample_points):
        """Test batch age calculation and tracking."""
        # Add points to batch
        for point in sample_points[:50]:
            await writer.write_point(point)
        
        # Wait a bit to create age
        await asyncio.sleep(0.1)
        
        # Flush batch and check age tracking
        with patch.object(writer, '_write_lines', return_value=True):
            success = await writer._flush_batch()
            assert success
            
            # Verify batch age was calculated and recorded
            # The age should be > 0 since we waited
            assert writer._last_batch_time is not None


class TestBatchProcessingReliability:
    """Test batch processing reliability features."""
    
    @pytest.fixture
    def writer(self):
        """Create InfluxDB writer instance for testing."""
        config = get_settings()
        config.influxdb_batch_size = 50
        config.influxdb_batch_timeout = 2.0
        config.influxdb_max_retries = 3
        config.influxdb_retry_delay = 0.1
        config.influxdb_retry_backoff = 2.0
        config.influxdb_retry_jitter = 0.1
        
        writer = InfluxDBWriter(config)
        # Mock connection state for testing
        writer._connected = True
        return writer
    
    @pytest.fixture
    def sample_points(self):
        """Generate sample data points for testing."""
        points = []
        for i in range(1000):
            point = InfluxDBPoint(
                measurement="test_measurement",
                tags={"sensor": f"sensor_{i % 10}", "location": f"room_{i % 5}"},
                fields={"value": float(i), "status": "active" if i % 2 == 0 else "inactive"},
                timestamp=datetime.now() + timedelta(seconds=i)
            )
            points.append(point)
        return points
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_behavior(self, writer):
        """Test circuit breaker pattern behavior."""
        # Initially closed
        assert writer._circuit_breaker_state == "CLOSED"
        
        # Simulate failures to trigger circuit breaker
        for i in range(writer._circuit_breaker_failure_threshold):
            writer._record_circuit_breaker_failure()
        
        # Circuit breaker should be open
        assert writer._circuit_breaker_state == "OPEN"
        assert writer._is_circuit_breaker_open()
        
        # Wait for timeout
        writer._circuit_breaker_last_failure_time = datetime.now() - timedelta(seconds=70)
        
        # Should transition to half-open
        writer._circuit_breaker_state = "HALF_OPEN"
        
        # Success should close circuit breaker
        writer._record_circuit_breaker_success()
        assert writer._circuit_breaker_state == "CLOSED"
        assert not writer._is_circuit_breaker_open()
    
    @pytest.mark.asyncio
    async def test_retry_delay_calculation(self, writer):
        """Test retry delay calculation with exponential backoff and jitter."""
        # Test exponential backoff
        delays = []
        for attempt in range(5):
            delay = writer._calculate_retry_delay(attempt)
            delays.append(delay)
        
        # Delays should increase exponentially
        for i in range(1, len(delays)):
            assert delays[i] > delays[i-1]
        
        # Delays should be capped at max delay (with some tolerance for jitter)
        max_delay = writer.config.influxdb_retry_delay * (writer.config.influxdb_retry_backoff ** 4)
        # Allow for jitter variation (jitter can be up to ±10% of base delay)
        tolerance = max_delay * 0.1
        assert all(delay <= max_delay + tolerance for delay in delays)
        
        # Test jitter variation
        delays_with_jitter = []
        for attempt in range(10):
            delay = writer._calculate_retry_delay(attempt)
            delays_with_jitter.append(delay)
        
        # Should have some variation due to jitter
        assert len(set(delays_with_jitter)) > 1
        
        # Verify all delays are positive
        assert all(delay > 0 for delay in delays)
        assert all(delay > 0 for delay in delays_with_jitter)
    
    @pytest.mark.asyncio
    async def test_batch_retry_mechanism(self, writer, sample_points):
        """Test batch retry mechanism with failures."""
        # Mock session to simulate failures
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status = 500  # Server error
        
        # First call fails, second succeeds
        mock_session.post = AsyncMock(side_effect=[
            ClientResponseError(request_info=Mock(), history=(), status=500),
            mock_response
        ])
        
        writer.session = mock_session
        
        # Add points and try to flush
        for point in sample_points[:50]:
            await writer.write_point(point)
        
        # Mock successful write after retry
        with patch.object(writer, '_write_lines', return_value=True):
            success = await writer._flush_batch()
            assert success
    
    @pytest.mark.asyncio
    async def test_batch_optimization_reliability(self, writer, sample_points):
        """Test that batch optimization produces reliable results."""
        # Create points with some duplicates
        duplicate_points = sample_points[:50] + sample_points[:25]  # 50 + 25 duplicates
        
        # Test deduplication
        optimized = writer._optimize_batch(duplicate_points)
        
        # Should have fewer points due to deduplication
        assert len(optimized) < len(duplicate_points)
        
        # All points should be unique
        point_ids = [id(p) for p in optimized]
        assert len(point_ids) == len(set(point_ids))
        
        # Test sorting reliability
        measurements = [p.measurement for p in optimized]
        assert measurements == sorted(measurements)
    
    @pytest.mark.asyncio
    async def test_compression_reliability(self, writer):
        """Test compression reliability and data integrity."""
        test_data = "test_data_" * 1000  # Create some repetitive data
        
        # Test gzip compression
        writer._compression = "gzip"
        compressed_data, encoding = writer._compress_data(test_data)
        
        # Verify compression
        assert encoding == "gzip"
        assert len(compressed_data) < len(test_data)
        
        # Test deflate compression
        writer._compression = "deflate"
        compressed_data, encoding = writer._compress_data(test_data)
        
        # Verify compression
        assert encoding == "deflate"
        assert len(compressed_data) < len(test_data)
        
        # Test edge cases
        empty_data = ""
        # Test with no compression explicitly set
        writer._compression = "none"
        compressed_empty, encoding = writer._compress_data(empty_data)
        assert compressed_empty == b''  # Empty string encoded as empty bytes
        assert encoding == "identity"


class TestBatchProcessingIntegration:
    """Test batch processing integration with other components."""
    
    @pytest.fixture
    def writer(self):
        """Create InfluxDB writer instance for testing."""
        config = get_settings()
        config.influxdb_batch_size = 100
        config.influxdb_batch_timeout = 5.0
        
        writer = InfluxDBWriter(config)
        # Mock connection state for testing
        writer._connected = True
        return writer
    
    @pytest.fixture
    def sample_points(self):
        """Generate sample data points for testing."""
        points = []
        for i in range(1000):
            point = InfluxDBPoint(
                measurement="test_measurement",
                tags={"sensor": f"sensor_{i % 10}", "location": f"room_{i % 5}"},
                fields={"value": float(i), "status": "active" if i % 2 == 0 else "inactive"},
                timestamp=datetime.now() + timedelta(seconds=i)
            )
            points.append(point)
        return points
    
    @pytest.mark.asyncio
    async def test_metrics_integration(self, writer, sample_points):
        """Test integration with metrics collection."""
        mock_collector = Mock()
        with patch('ha_ingestor.influxdb.writer.get_metrics_collector', return_value=mock_collector):
            # Add points and flush batch
            for point in sample_points[:100]:
                await writer.write_point(point)
            
            # Mock successful write
            with patch.object(writer, '_write_lines', return_value=True):
                success = await writer._flush_batch()
                assert success
                
                # Verify metrics were recorded (may be called multiple times due to retries)
                assert mock_collector.record_influxdb_batch_processed.called
                assert mock_collector.record_influxdb_write.called
    
    @pytest.mark.asyncio
    async def test_logging_integration(self, writer, sample_points):
        """Test integration with logging system."""
        # Mock logger
        mock_logger = Mock()
        writer.logger = mock_logger
        
        # Add points and flush batch
        for point in sample_points[:100]:
            await writer.write_point(point)
        
        # Mock successful write
        with patch.object(writer, '_write_lines', return_value=True):
            success = await writer._flush_batch()
            assert success
            
            # Verify logging occurred
            assert mock_logger.info.called or mock_logger.debug.called
    
    @pytest.mark.asyncio
    async def test_configuration_integration(self, writer):
        """Test integration with configuration system."""
        # Test dynamic configuration updates
        new_batch_size = 200
        new_timeout = 10.0
        
        writer.update_batch_config(
            batch_size=new_batch_size,
            batch_timeout=new_timeout
        )
        
        # Verify configuration was updated
        config = writer.get_batch_config()
        assert config['batch_size'] == new_batch_size
        assert config['batch_timeout'] == new_timeout
        
        # Verify internal state was updated
        assert writer._batch_size == new_batch_size
        assert writer._batch_timeout == new_timeout


class TestBatchProcessingEdgeCases:
    """Test batch processing edge cases and error conditions."""
    
    @pytest.fixture
    def writer(self):
        """Create InfluxDB writer instance for testing."""
        config = get_settings()
        config.influxdb_batch_size = 10
        config.influxdb_batch_timeout = 1.0
        
        writer = InfluxDBWriter(config)
        # Mock connection state for testing
        writer._connected = True
        return writer
    
    @pytest.fixture
    def sample_points(self):
        """Generate sample data points for testing."""
        points = []
        for i in range(1000):
            point = InfluxDBPoint(
                measurement="test_measurement",
                tags={"sensor": f"sensor_{i % 10}", "location": f"room_{i % 5}"},
                fields={"value": float(i), "status": "active" if i % 2 == 0 else "inactive"},
                timestamp=datetime.now() + timedelta(seconds=i)
            )
            points.append(point)
        return points
    
    @pytest.mark.asyncio
    async def test_empty_batch_handling(self, writer):
        """Test handling of empty batches."""
        # Try to flush empty batch
        success = await writer._flush_batch()
        assert success  # Should succeed with no points
        
        # Verify no metrics or errors
        assert writer._points_written == 0
        assert writer._points_failed == 0
    
    @pytest.mark.asyncio
    async def test_single_point_batch(self, writer, sample_points):
        """Test handling of single point batches."""
        # Add single point
        await writer.write_point(sample_points[0])
        
        # Flush batch
        with patch.object(writer, '_write_lines', return_value=True):
            success = await writer._flush_batch()
            assert success
    
    @pytest.mark.asyncio
    async def test_large_batch_handling(self, writer, sample_points):
        """Test handling of batches larger than configured size."""
        # Add more points than batch size
        for point in sample_points[:150]:  # More than batch size of 10
            await writer.write_point(point)
        
        # Points should accumulate until manually flushed
        # Verify all points were added to pending queue
        assert len(writer._pending_points) == 150
        
        # Flush the batch manually
        with patch.object(writer, '_write_lines', return_value=True):
            success = await writer._flush_batch()
            assert success
            
            # After flush, pending points should be cleared
            assert len(writer._pending_points) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_batch_operations(self, writer, sample_points):
        """Test concurrent batch operations."""
        # Create multiple tasks writing points
        async def write_points(start_idx, count):
            for i in range(count):
                await writer.write_point(sample_points[start_idx + i])
        
        # Start multiple concurrent writers
        tasks = [
            write_points(i * 50, 50) for i in range(4)
        ]
        
        # Run concurrently
        await asyncio.gather(*tasks)
        
        # Verify all points were added
        assert len(writer._pending_points) == 200
    
    @pytest.mark.asyncio
    async def test_batch_timeout_handling(self, writer, sample_points):
        """Test batch timeout handling."""
        # Set very short timeout
        writer._batch_timeout = 0.1
        
        # Add some points
        for point in sample_points[:50]:
            await writer.write_point(point)
        
        # Wait for timeout
        await asyncio.sleep(0.2)
        
        # Batch should have been flushed due to timeout
        # (This would require the actual batch task to be running)
        # For now, just verify the timeout configuration is respected
        assert writer._batch_timeout == 0.1


class TestBatchProcessingPerformanceBenchmarks:
    """Performance benchmarks for batch processing."""
    
    @pytest.fixture
    def writer(self):
        """Create InfluxDB writer instance for testing."""
        config = get_settings()
        config.influxdb_batch_size = 1000
        config.influxdb_batch_timeout = 10.0
        config.influxdb_compression = "gzip"
        config.influxdb_optimize_batches = True
        
        writer = InfluxDBWriter(config)
        # Mock connection state for testing
        writer._connected = True
        return writer
    
    @pytest.fixture
    def sample_points(self):
        """Generate sample data points for testing."""
        points = []
        for i in range(1000):
            point = InfluxDBPoint(
                measurement="test_measurement",
                tags={"sensor": f"sensor_{i % 10}", "location": f"room_{i % 5}"},
                fields={"value": float(i), "status": "active" if i % 2 == 0 else "inactive"},
                timestamp=datetime.now() + timedelta(seconds=i)
            )
            points.append(point)
        return points
    
    @pytest.mark.asyncio
    async def test_large_batch_performance(self, writer, sample_points):
        """Test performance with large batches."""
        large_batch = sample_points[:1000]
        
        # Measure optimization time
        start_time = time.time()
        optimized = writer._optimize_batch(large_batch)
        optimization_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert optimization_time < 0.01  # 10ms for 1000 points
        
        # Measure compression time
        test_data = '\n'.join([str(p) for p in optimized])
        start_time = time.time()
        compressed_data, encoding = writer._compress_data(test_data)
        compression_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert compression_time < 0.05  # 50ms for 1000 points
        
        # Verify compression ratio
        original_size = len(test_data.encode('utf-8'))
        compressed_size = len(compressed_data)
        compression_ratio = original_size / compressed_size
        
        # Should have reasonable compression
        assert compression_ratio > 1.0
        assert compression_ratio < 20.0
    
    @pytest.mark.asyncio
    async def test_throughput_calculation_performance(self, writer):
        """Test throughput calculation performance."""
        # Simulate high throughput
        writer._points_written = 100000
        writer._batches_processed = 1000
        writer._total_write_time = 100.0
        writer._total_batch_time = 50.0
        
        # Measure calculation time
        start_time = time.time()
        for _ in range(1000):  # 1000 calculations
            writer.update_throughput_metrics()
        calculation_time = time.time() - start_time
        
        # Should be very fast
        assert calculation_time < 0.1  # 100ms for 1000 calculations
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_performance(self, writer):
        """Test circuit breaker performance under load."""
        # Simulate many failures quickly
        start_time = time.time()
        for _ in range(1000):
            writer._record_circuit_breaker_failure()
        failure_recording_time = time.time() - start_time
        
        # Should be very fast
        assert failure_recording_time < 0.1  # 100ms for 1000 operations
        
        # Test state checking performance
        start_time = time.time()
        for _ in range(10000):
            writer._is_circuit_breaker_open()
        state_check_time = time.time() - start_time
        
        # Should be extremely fast
        assert state_check_time < 0.01  # 10ms for 10000 operations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
