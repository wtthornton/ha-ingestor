"""Tests for enhanced logging functionality."""

import pytest
import logging
import tempfile
import os
from unittest.mock import patch, MagicMock

from ha_ingestor.utils.logging import (
    setup_logging,
    get_logger,
    set_correlation_id,
    get_correlation_id,
    add_log_context,
    clear_log_context,
    log_with_context,
    LogContextManager,
    log_context,
    log_function_call,
    log_performance,
)


class TestEnhancedLogging:
    """Test enhanced logging functionality."""

    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        with patch('ha_ingestor.utils.logging.get_settings') as mock_get_settings:
            mock_config = MagicMock()
            mock_config.log_level = "DEBUG"
            mock_config.log_format = "console"
            mock_config.service_name = "test-service"
            mock_get_settings.return_value = mock_config
            
            setup_logging()
            
            # Verify structlog was configured
            import structlog
            assert structlog.is_configured()

    def test_correlation_id_management(self):
        """Test correlation ID generation and management."""
        # Test setting correlation ID
        correlation_id = set_correlation_id()
        assert correlation_id is not None
        assert len(correlation_id) > 0
        
        # Test getting correlation ID
        retrieved_id = get_correlation_id()
        assert retrieved_id == correlation_id
        
        # Test setting custom correlation ID
        custom_id = "custom-123"
        set_correlation_id(custom_id)
        assert get_correlation_id() == custom_id

    def test_log_context_management(self):
        """Test log context management."""
        # Test adding context
        add_log_context(user_id="123", operation="test")
        
        # Test getting context
        from ha_ingestor.utils.logging import _log_context
        context = _log_context.get()
        assert context["user_id"] == "123"
        assert context["operation"] == "test"
        
        # Test clearing context
        clear_log_context()
        context = _log_context.get()
        assert context == {}

    def test_log_context_manager(self):
        """Test LogContextManager context manager."""
        # Set initial context
        add_log_context(initial="value")
        
        # Use context manager
        with LogContextManager(temp_key="temp_value"):
            context = _log_context.get()
            assert context["initial"] == "value"
            assert context["temp_key"] == "temp_value"
        
        # Context should be restored
        context = _log_context.get()
        assert context["initial"] == "value"
        assert "temp_key" not in context

    def test_log_context_decorator(self):
        """Test log_context decorator."""
        @log_context(decorator_key="decorator_value")
        def test_function():
            context = _log_context.get()
            assert context["decorator_key"] == "decorator_value"
            return "success"
        
        result = test_function()
        assert result == "success"
        
        # Context should be cleared after function
        context = _log_context.get()
        assert "decorator_key" not in context

    def test_log_with_context(self):
        """Test log_with_context function."""
        logger = get_logger(__name__)
        
        # Set some context
        add_log_context(user_id="456")
        set_correlation_id("test-correlation")
        
        # Test logging with context
        with patch.object(logger, 'info') as mock_info:
            log_with_context(logger, "Test message", additional="data")
            
            # Verify context was added
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[0][0] == "Test message"
            assert call_args[1]["user_id"] == "456"
            assert call_args[1]["correlation_id"] == "test-correlation"
            assert call_args[1]["additional"] == "data"

    def test_log_function_call_decorator(self):
        """Test log_function_call decorator."""
        @log_function_call("test_function", include_args=True, include_result=True)
        def test_function(param1, param2):
            return f"result: {param1} + {param2}"
        
        with patch('ha_ingestor.utils.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_function("a", "b")
            
            # Verify function executed
            assert result == "result: a + b"
            
            # Verify logging calls
            assert mock_logger.debug.call_count >= 2  # Entry and completion

    def test_log_performance_decorator(self):
        """Test log_performance decorator."""
        @log_performance("test_operation", log_level="INFO")
        def test_operation():
            import time
            time.sleep(0.01)  # Small delay for timing
            return "operation_complete"
        
        with patch('ha_ingestor.utils.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_operation()
            
            # Verify function executed
            assert result == "operation_complete"
            
            # Verify logging calls
            assert mock_logger.log.call_count >= 2  # Start and completion

    def test_log_rotation_configuration(self):
        """Test log rotation configuration."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            with patch('ha_ingestor.utils.logging.get_settings') as mock_get_settings:
                mock_config = MagicMock()
                mock_config.log_level = "INFO"
                mock_config.log_format = "json"
                mock_config.service_name = "test-service"
                mock_config.log_file = temp_file_path
                mock_config.log_max_size = 1024  # 1KB
                mock_config.log_backup_count = 3
                mock_get_settings.return_value = mock_config
                
                setup_logging()
                
                # Verify log file was created
                assert os.path.exists(temp_file_path)
                
        finally:
            # Cleanup
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_environment_info_logging(self):
        """Test that environment information is added to logs."""
        with patch('ha_ingestor.utils.logging.get_settings') as mock_get_settings:
            mock_config = MagicMock()
            mock_config.log_level = "INFO"
            mock_config.log_format = "json"
            mock_config.service_name = "test-service"
            mock_get_settings.return_value = mock_config
            
            setup_logging()
            
            logger = get_logger(__name__)
            
            # Test that environment info is included
            with patch.object(logger, 'info') as mock_info:
                logger.info("Test message")
                
                # Verify environment info was added
                call_args = mock_info.call_args
                assert "environment" in call_args[1]
                assert "hostname" in call_args[1]

    def test_enhanced_logging_fallback(self):
        """Test logging fallback when configuration fails."""
        with patch('ha_ingestor.utils.logging.get_settings', side_effect=Exception("Config error")):
            with patch('logging.basicConfig') as mock_basic_config:
                from ha_ingestor.utils.logging import setup_default_logging
                setup_default_logging()
                
                # Verify fallback logging was configured
                mock_basic_config.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
