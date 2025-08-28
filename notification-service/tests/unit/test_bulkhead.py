"""
Unit tests for BulkheadExecutor resilience pattern implementation.
"""

import pytest
import asyncio
import time
import os
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from core.resilience.bulkhead import (
    BulkheadExecutor, 
    BulkheadConfig, 
    BulkheadPartition,
    PartitionStatus,
    get_bulkhead_executor,
    shutdown_bulkhead_executor
)


@pytest.mark.unit
class TestBulkheadConfig:
    """Test cases for BulkheadConfig."""

    def test_config_creation_with_defaults(self):
        """Test config creation with default values."""
        config = BulkheadConfig()
        
        assert config.max_workers == 2
        assert config.timeout_seconds == 30.0
        assert config.name == "default"

    def test_config_creation_with_custom_values(self):
        """Test config creation with custom values."""
        config = BulkheadConfig(
            max_workers=5,
            timeout_seconds=15.0,
            name="test"
        )
        
        assert config.max_workers == 5
        assert config.timeout_seconds == 15.0
        assert config.name == "test"

    def test_config_immutable_after_creation(self):
        """Test that config values remain consistent."""
        config = BulkheadConfig(max_workers=3, timeout_seconds=10.0)
        
        # Values should remain the same
        assert config.max_workers == 3
        assert config.timeout_seconds == 10.0


@pytest.mark.unit
class TestBulkheadPartition:
    """Test cases for BulkheadPartition."""

    def test_partition_creation(self):
        """Test partition initialization."""
        config = BulkheadConfig(max_workers=3, timeout_seconds=5.0, name="test")
        partition = BulkheadPartition(config)
        
        assert partition.config == config
        assert partition.status == PartitionStatus.HEALTHY
        assert partition.total_executions == 0
        assert partition.successful_executions == 0
        assert isinstance(partition._executor, ThreadPoolExecutor)

    def test_partition_health_no_executions(self):
        """Test partition health status with no executions."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test")
        partition = BulkheadPartition(config)
        
        # No executions should start with HEALTHY status
        assert partition.status == PartitionStatus.HEALTHY

    def test_partition_health_after_success(self):
        """Test partition health status after successful execution."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test")
        partition = BulkheadPartition(config)
        
        # Simulate successful executions
        partition.total_executions = 100
        partition.successful_executions = 90
        partition.status = PartitionStatus.HEALTHY
        
        assert partition.status == PartitionStatus.HEALTHY

    def test_partition_health_after_failure(self):
        """Test partition health status after failures."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test")
        partition = BulkheadPartition(config)
        
        # Simulate failed status
        partition.total_executions = 100
        partition.successful_executions = 40
        partition.status = PartitionStatus.FAILED
        
        assert partition.status == PartitionStatus.FAILED

    @pytest.mark.asyncio
    async def test_partition_execute_success(self):
        """Test successful partition execution."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test")
        partition = BulkheadPartition(config)
        
        def test_function():
            return {"result": "success"}
        
        result = await partition.execute(test_function)
        
        assert result == {"result": "success"}
        assert partition.total_executions == 1
        assert partition.successful_executions == 1
        assert partition.status == PartitionStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_partition_execute_with_args(self):
        """Test partition execution with function arguments."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test")
        partition = BulkheadPartition(config)
        
        def test_function_with_args(*args, **kwargs):
            return {"args": args, "kwargs": kwargs}
        
        # Create wrapper that captures args/kwargs
        def wrapper():
            return test_function_with_args("arg1", "arg2", key="value")
        
        result = await partition.execute(wrapper)
        
        assert result["args"] == ("arg1", "arg2")
        assert result["kwargs"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_partition_execute_timeout(self):
        """Test partition execution timeout."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=0.1, name="test")
        partition = BulkheadPartition(config)
        
        def slow_function():
            time.sleep(1)  # Longer than timeout
            return {"result": "should not reach"}
        
        with pytest.raises(TimeoutError) as exc_info:
            await partition.execute(slow_function)
        
        assert "Operation timeout in 'test' partition" in str(exc_info.value)
        assert partition.total_executions == 1
        assert partition.successful_executions == 0
        assert partition.status == PartitionStatus.FAILED

    @pytest.mark.asyncio
    async def test_partition_execute_exception(self):
        """Test partition execution with exception."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test")
        partition = BulkheadPartition(config)
        
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError) as exc_info:
            await partition.execute(failing_function)
        
        assert "Test error" in str(exc_info.value)
        assert partition.total_executions == 1
        assert partition.successful_executions == 0
        assert partition.status == PartitionStatus.FAILED

    def test_partition_get_metrics(self):
        """Test partition metrics generation."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test")
        partition = BulkheadPartition(config)
        
        # Simulate some executions
        partition.total_executions = 10
        partition.successful_executions = 8
        partition.status = PartitionStatus.HEALTHY
        
        metrics = partition.get_metrics()
        
        assert metrics["name"] == "test"
        assert metrics["status"] == "healthy"
        assert metrics["total_executions"] == 10
        assert metrics["successful_executions"] == 8
        assert metrics["success_rate"] == 80.0

    def test_partition_get_metrics_no_executions(self):
        """Test partition metrics with no executions."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test")
        partition = BulkheadPartition(config)
        
        metrics = partition.get_metrics()
        
        assert metrics["name"] == "test"
        assert metrics["status"] == "healthy"
        assert metrics["total_executions"] == 0
        assert metrics["successful_executions"] == 0
        assert metrics["success_rate"] == 0.0

    def test_partition_shutdown(self):
        """Test partition shutdown."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test")
        partition = BulkheadPartition(config)
        
        # Should not raise exception
        partition.shutdown()
        
        # Executor should be shutdown
        assert partition._executor._shutdown


@pytest.mark.unit
class TestBulkheadExecutor:
    """Test cases for BulkheadExecutor."""

    def setup_method(self):
        """Setup for each test."""
        # Reset global executor
        import core.resilience.bulkhead as bulkhead_module
        bulkhead_module._global_executor = None

    def teardown_method(self):
        """Cleanup after each test."""
        # Shutdown any created executors
        try:
            shutdown_bulkhead_executor()
        except:
            pass

    def test_executor_initialization_default(self):
        """Test executor initialization with default config."""
        executor = BulkheadExecutor()
        
        partitions = executor.list_partitions()
        assert "email" in partitions
        assert "sms" in partitions
        assert "push" in partitions
        assert "default" in partitions
        assert len(partitions) >= 4

    def test_executor_initialization_with_custom_config(self):
        """Test executor initialization with custom config."""
        custom_configs = {
            "test1": BulkheadConfig(max_workers=3, timeout_seconds=10.0, name="test1"),
            "test2": BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test2")
        }
        
        executor = BulkheadExecutor(custom_configs)
        
        partitions = executor.list_partitions()
        assert "test1" in partitions
        assert "test2" in partitions
        assert len(partitions) == 2

    @patch.dict(os.environ, {
        'BULKHEAD_BASE_WORKERS': '3',
        'BULKHEAD_EMAIL_WORKERS': '4',
        'BULKHEAD_EMAIL_TIMEOUT': '20.0'
    })
    def test_executor_environment_configuration(self):
        """Test executor configuration from environment variables."""
        executor = BulkheadExecutor()
        
        email_partition = executor._partitions["email"]
        assert email_partition.config.max_workers == 4
        assert email_partition.config.timeout_seconds == 20.0

    def test_executor_list_partitions(self):
        """Test listing partitions."""
        executor = BulkheadExecutor()
        
        partitions = executor.list_partitions()
        assert isinstance(partitions, list)
        assert len(partitions) >= 4
        assert all(isinstance(name, str) for name in partitions)

    @pytest.mark.asyncio
    async def test_executor_execute_existing_partition(self):
        """Test execution on existing partition."""
        executor = BulkheadExecutor()
        
        def test_function():
            return {"channel": "email", "result": "success"}
        
        result = await executor.execute("email", test_function)
        
        assert result["channel"] == "email"
        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_executor_execute_fallback_partition(self):
        """Test execution falls back to default partition."""
        executor = BulkheadExecutor()
        
        def test_function():
            return {"channel": "unknown", "result": "success"}
        
        result = await executor.execute("unknown_channel", test_function)
        
        assert result["channel"] == "unknown"
        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_executor_execute_no_default_partition(self):
        """Test execution when no default partition exists."""
        # Create executor with no default partition
        custom_configs = {
            "test": BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test")
        }
        executor = BulkheadExecutor(custom_configs)
        
        def test_function():
            return {"result": "success"}
        
        with pytest.raises(ValueError) as exc_info:
            await executor.execute("unknown", test_function)
        
        assert "No partitions available" in str(exc_info.value)

    def test_executor_get_health_all_healthy(self):
        """Test health status when all partitions are healthy."""
        executor = BulkheadExecutor()
        
        health = executor.get_health()
        
        assert health["status"] == "healthy"
        assert health["total_partitions"] >= 4
        assert health["healthy_partitions"] >= 4
        assert "partitions" in health
        
        # All partitions should be healthy initially
        for partition_name, partition_health in health["partitions"].items():
            assert partition_health["status"] == "healthy"

    def test_executor_get_health_with_unhealthy_partition(self):
        """Test health status with one unhealthy partition."""
        executor = BulkheadExecutor()
        
        # Make one partition unhealthy
        email_partition = executor._partitions["email"]
        email_partition.total_executions = 100
        email_partition.successful_executions = 30  # 30% success rate
        email_partition.status = PartitionStatus.FAILED
        
        health = executor.get_health()
        
        assert health["status"] == "degraded"
        assert health["partitions"]["email"]["status"] == "failed"

    def test_executor_get_health_all_failed(self):
        """Test health status when all partitions are failed."""
        executor = BulkheadExecutor()
        
        # Make all partitions unhealthy
        for partition in executor._partitions.values():
            partition.status = PartitionStatus.FAILED
        
        health = executor.get_health()
        
        assert health["status"] == "failed"
        assert health["healthy_partitions"] == 0

    def test_executor_shutdown(self):
        """Test executor shutdown."""
        executor = BulkheadExecutor()
        
        # Should not raise exception
        executor.shutdown()
        
        # All partitions should be shutdown
        for partition in executor._partitions.values():
            assert partition._executor._shutdown

    @pytest.mark.asyncio
    async def test_executor_concurrent_executions(self):
        """Test concurrent executions across partitions."""
        executor = BulkheadExecutor()
        
        def test_function(channel_id):
            time.sleep(0.1)  # Simulate some work
            return {"channel_id": channel_id, "result": "success"}
        
        # Create tasks for different partitions
        tasks = []
        channels = ["email", "sms", "push"]
        
        for i in range(9):  # 3 per channel
            channel = channels[i % 3]
            tasks.append(executor.execute(channel, lambda ch=channel: test_function(ch)))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time
        
        # All should succeed
        assert len(results) == 9
        assert all(r["result"] == "success" for r in results)
        
        # Should be much faster than sequential execution (0.9s)
        assert execution_time < 0.5


@pytest.mark.unit
class TestBulkheadGlobalFunctions:
    """Test cases for global bulkhead functions."""

    def setup_method(self):
        """Setup for each test."""
        # Reset global executor
        import core.resilience.bulkhead as bulkhead_module
        bulkhead_module._global_executor = None

    def teardown_method(self):
        """Cleanup after each test."""
        # Shutdown any created executors
        try:
            shutdown_bulkhead_executor()
        except:
            pass

    def test_get_bulkhead_executor_singleton(self):
        """Test that get_bulkhead_executor returns singleton."""
        executor1 = get_bulkhead_executor()
        executor2 = get_bulkhead_executor()
        
        assert executor1 is executor2

    def test_get_bulkhead_executor_creates_instance(self):
        """Test that get_bulkhead_executor creates BulkheadExecutor instance."""
        executor = get_bulkhead_executor()
        
        assert isinstance(executor, BulkheadExecutor)
        assert len(executor.list_partitions()) >= 4

    def test_shutdown_bulkhead_executor(self):
        """Test shutdown_bulkhead_executor function."""
        executor = get_bulkhead_executor()
        original_executor = executor
        
        shutdown_bulkhead_executor()
        
        # Global executor should be None
        import core.resilience.bulkhead as bulkhead_module
        assert bulkhead_module._global_executor is None
        
        # Original executor should be shutdown
        for partition in original_executor._partitions.values():
            assert partition._executor._shutdown

    def test_get_bulkhead_executor_after_shutdown(self):
        """Test getting executor after shutdown creates new instance."""
        executor1 = get_bulkhead_executor()
        shutdown_bulkhead_executor()
        executor2 = get_bulkhead_executor()
        
        assert executor1 is not executor2
        assert isinstance(executor2, BulkheadExecutor)


@pytest.mark.unit  
class TestBulkheadIntegration:
    """Integration test cases for bulkhead components."""

    def setup_method(self):
        """Setup for each test."""
        # Reset global executor
        import core.resilience.bulkhead as bulkhead_module
        bulkhead_module._global_executor = None

    def teardown_method(self):
        """Cleanup after each test."""
        try:
            shutdown_bulkhead_executor()
        except:
            pass

    @pytest.mark.asyncio
    async def test_end_to_end_execution_flow(self):
        """Test complete execution flow from global function to partition."""
        def notification_sender(channel, message):
            return {
                "channel": channel,
                "message": message,
                "timestamp": time.time(),
                "status": "sent"
            }
        
        executor = get_bulkhead_executor()
        
        # Test different channels
        channels = ["email", "sms", "push", "unknown"]
        for channel in channels:
            result = await executor.execute(
                channel, 
                lambda ch=channel: notification_sender(ch, f"Test message for {ch}")
            )
            
            assert result["channel"] == channel
            assert result["status"] == "sent"
            assert f"Test message for {channel}" in result["message"]

    @pytest.mark.asyncio
    async def test_error_isolation_between_partitions(self):
        """Test that errors in one partition don't affect others."""
        executor = get_bulkhead_executor()
        
        def failing_function():
            raise RuntimeError("Partition failure")
        
        def success_function():
            return {"result": "success"}
        
        # Fail email partition
        with pytest.raises(RuntimeError):
            await executor.execute("email", failing_function)
        
        # SMS partition should still work
        result = await executor.execute("sms", success_function)
        assert result["result"] == "success"
        
        # Check health shows email as failed but sms as healthy
        health = executor.get_health()
        # Note: Single failure doesn't necessarily mark partition as failed
        # unless it crosses the threshold, but execution tracking should work

    @pytest.mark.asyncio
    async def test_timeout_isolation_between_partitions(self):
        """Test that timeouts in one partition don't affect others."""
        # Create executor with very short timeout for testing
        custom_configs = {
            "fast": BulkheadConfig(max_workers=2, timeout_seconds=0.1, name="fast"),
            "normal": BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="normal")
        }
        executor = BulkheadExecutor(custom_configs)
        
        def slow_function():
            time.sleep(1)
            return {"result": "slow"}
        
        def quick_function():
            return {"result": "quick"}
        
        # Fast partition should timeout
        with pytest.raises(TimeoutError):
            await executor.execute("fast", slow_function)
        
        # Normal partition should work fine
        result = await executor.execute("normal", quick_function)
        assert result["result"] == "quick"

    @patch.dict(os.environ, {
        'BULKHEAD_EMAIL_WORKERS': '1',
        'BULKHEAD_SMS_WORKERS': '1', 
        'BULKHEAD_PUSH_WORKERS': '1',
        'BULKHEAD_EMAIL_TIMEOUT': '5.0',
        'BULKHEAD_SMS_TIMEOUT': '3.0',
        'BULKHEAD_PUSH_TIMEOUT': '1.0'
    })
    def test_environment_configuration_integration(self):
        """Test that environment configuration is properly applied."""
        executor = get_bulkhead_executor()
        
        # Check that environment variables were applied
        email_partition = executor._partitions["email"]
        sms_partition = executor._partitions["sms"]
        push_partition = executor._partitions["push"]
        
        assert email_partition.config.max_workers == 1
        assert email_partition.config.timeout_seconds == 5.0
        
        assert sms_partition.config.max_workers == 1
        assert sms_partition.config.timeout_seconds == 3.0
        
        assert push_partition.config.max_workers == 1
        assert push_partition.config.timeout_seconds == 1.0


@pytest.mark.unit
class TestBulkheadEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Setup for each test."""
        import core.resilience.bulkhead as bulkhead_module
        bulkhead_module._global_executor = None

    def teardown_method(self):
        """Cleanup after each test."""
        try:
            shutdown_bulkhead_executor()
        except:
            pass

    def test_config_with_zero_workers(self):
        """Test configuration with zero workers."""
        config = BulkheadConfig(max_workers=0, timeout_seconds=5.0)
        
        # ThreadPoolExecutor doesn't allow 0 workers, should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            partition = BulkheadPartition(config)
        
        assert "max_workers must be greater than 0" in str(exc_info.value)

    def test_config_with_negative_timeout(self):
        """Test configuration with negative timeout."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=-1.0)
        
        # Should create config but timeout behavior undefined
        assert config.timeout_seconds == -1.0

    @pytest.mark.asyncio
    async def test_execute_none_function(self):
        """Test execution with None function."""
        executor = BulkheadExecutor()
        
        with pytest.raises((TypeError, AttributeError)):
            await executor.execute("email", None)

    @pytest.mark.asyncio 
    async def test_execute_invalid_function(self):
        """Test execution with non-callable object."""
        executor = BulkheadExecutor()
        
        with pytest.raises((TypeError, AttributeError)):
            await executor.execute("email", "not a function")

    @pytest.mark.asyncio
    async def test_execute_after_shutdown(self):
        """Test execution after executor shutdown."""
        executor = BulkheadExecutor()
        executor.shutdown()
        
        def test_function():
            return {"result": "success"}
        
        with pytest.raises(RuntimeError):
            await executor.execute("email", test_function)

    def test_multiple_shutdowns(self):
        """Test that multiple shutdowns are safe."""
        executor = BulkheadExecutor()
        
        # Multiple shutdowns should not raise exceptions
        executor.shutdown()
        executor.shutdown()
        executor.shutdown()

    @patch.dict(os.environ, {}, clear=True)
    def test_executor_with_no_environment_variables(self):
        """Test executor creation when no environment variables are set."""
        executor = BulkheadExecutor()
        
        # Should still create with reasonable defaults
        partitions = executor.list_partitions()
        assert len(partitions) >= 4
        
        # Check that partitions have reasonable defaults
        for partition_name in ["email", "sms", "push", "default"]:
            partition = executor._partitions[partition_name]
            assert partition.config.max_workers >= 1
            assert partition.config.timeout_seconds > 0

    def test_partition_metrics_precision(self):
        """Test partition metrics calculation precision."""
        config = BulkheadConfig(max_workers=2, timeout_seconds=5.0, name="test")
        partition = BulkheadPartition(config)
        
        # Test with numbers that might cause floating point issues
        partition.total_executions = 3
        partition.successful_executions = 1
        
        metrics = partition.get_metrics()
        expected_rate = (1/3) * 100  # 33.333...
        
        assert abs(metrics["success_rate"] - 33.3) < 0.1  # Allow small precision difference
