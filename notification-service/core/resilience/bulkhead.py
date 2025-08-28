"""
BulkheadExecutor for Docker/Kubernetes deployments.

Container-optimized implementation focusing on resource isolation and fault tolerance
with minimal overhead and simple configuration.
"""

import asyncio
import logging
import time
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Optional, TypeVar
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)
T = TypeVar('T')


class PartitionStatus(Enum):
    """Simple partition status"""
    HEALTHY = "healthy"
    FAILED = "failed"


@dataclass
class BulkheadConfig:
    """Bulkhead partition configuration"""
    max_workers: int = 2
    timeout_seconds: float = 30.0
    name: str = "default"


class BulkheadPartition:
    """Bulkhead partition with resource isolation"""
    
    def __init__(self, config: BulkheadConfig):
        self.config = config
        self.status = PartitionStatus.HEALTHY
        self.total_executions = 0
        self.successful_executions = 0
        self._executor = ThreadPoolExecutor(
            max_workers=config.max_workers,
            thread_name_prefix=f"bulkhead-{config.name}"
        )
        
    async def execute(self, func: Callable[[], T]) -> T:
        """Execute function with timeout protection"""
        self.total_executions += 1
        
        try:
            logger.debug(f"Executing in bulkhead '{self.config.name}'")
            
            # Execute with timeout
            future = self._executor.submit(func)
            result = await asyncio.wait_for(
                asyncio.wrap_future(future),
                timeout=self.config.timeout_seconds
            )
            
            self.successful_executions += 1
            self.status = PartitionStatus.HEALTHY
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout in bulkhead '{self.config.name}' after {self.config.timeout_seconds}s")
            self.status = PartitionStatus.FAILED
            raise TimeoutError(f"Operation timeout in '{self.config.name}' partition")
            
        except Exception as e:
            logger.error(f"Error in bulkhead '{self.config.name}': {e}")
            self.status = PartitionStatus.FAILED
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get basic metrics"""
        success_rate = 0.0
        if self.total_executions > 0:
            success_rate = (self.successful_executions / self.total_executions) * 100
        
        return {
            "name": self.config.name,
            "status": self.status.value,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "success_rate": round(success_rate, 1)
        }
    
    def shutdown(self):
        """Shutdown the executor"""
        self._executor.shutdown(wait=False)


class BulkheadExecutor:
    """Container-optimized bulkhead executor for resource isolation"""
    
    def __init__(self, configs: Optional[Dict[str, BulkheadConfig]] = None):
        """Initialize with container-friendly defaults"""
        self._partitions: Dict[str, BulkheadPartition] = {}
        
        if configs is None:
            configs = self._get_container_configs()
            
        for name, config in configs.items():
            config.name = name
            self._partitions[name] = BulkheadPartition(config)
            logger.info(f"Initialized bulkhead '{name}' with {config.max_workers} workers")
    
    def _get_container_configs(self) -> Dict[str, BulkheadConfig]:
        """Get container-optimized configurations"""
        # Use environment variables or sensible container defaults
        base_workers = int(os.getenv('BULKHEAD_BASE_WORKERS', '2'))
        base_timeout = float(os.getenv('BULKHEAD_BASE_TIMEOUT', '30.0'))
        
        return {
            "email": BulkheadConfig(
                max_workers=int(os.getenv('BULKHEAD_EMAIL_WORKERS', str(base_workers))),
                timeout_seconds=float(os.getenv('BULKHEAD_EMAIL_TIMEOUT', str(base_timeout))),
                name="email"
            ),
            "sms": BulkheadConfig(
                max_workers=int(os.getenv('BULKHEAD_SMS_WORKERS', str(base_workers))),
                timeout_seconds=float(os.getenv('BULKHEAD_SMS_TIMEOUT', '15.0')),
                name="sms"
            ),
            "push": BulkheadConfig(
                max_workers=int(os.getenv('BULKHEAD_PUSH_WORKERS', str(base_workers + 1))),
                timeout_seconds=float(os.getenv('BULKHEAD_PUSH_TIMEOUT', '10.0')),
                name="push"
            ),
            "default": BulkheadConfig(
                max_workers=int(os.getenv('BULKHEAD_DEFAULT_WORKERS', str(base_workers))),
                timeout_seconds=float(os.getenv('BULKHEAD_DEFAULT_TIMEOUT', str(base_timeout))),
                name="default"
            )
        }
    
    async def execute(self, partition_name: str, func: Callable[[], T]) -> T:
        """Execute function in specified partition"""
        if partition_name not in self._partitions:
            # Fallback to default partition
            partition_name = "default"
            if partition_name not in self._partitions:
                raise ValueError(f"No partitions available")
        
        partition = self._partitions[partition_name]
        return await partition.execute(func)
    
    def get_health(self) -> Dict[str, Any]:
        """Get health status for monitoring"""
        partitions = {}
        healthy_count = 0
        total_count = len(self._partitions)
        
        for name, partition in self._partitions.items():
            metrics = partition.get_metrics()
            partitions[name] = metrics
            if partition.status == PartitionStatus.HEALTHY:
                healthy_count += 1
        
        overall_status = "healthy" if healthy_count == total_count else "degraded"
        if healthy_count == 0:
            overall_status = "failed"
        
        return {
            "status": overall_status,
            "partitions": partitions,
            "healthy_partitions": healthy_count,
            "total_partitions": total_count
        }
    
    def list_partitions(self) -> list[str]:
        """Get list of partition names"""
        return list(self._partitions.keys())
    
    def shutdown(self):
        """Shutdown all partitions"""
        logger.info("Shutting down BulkheadExecutor")
        for partition in self._partitions.values():
            partition.shutdown()
        logger.info("BulkheadExecutor shutdown complete")


# Global instance for container lifecycle
_executor: Optional[BulkheadExecutor] = None


def get_bulkhead_executor() -> BulkheadExecutor:
    """Get global bulkhead executor instance"""
    global _executor
    
    if _executor is None:
        logger.info("Initializing BulkheadExecutor")
        _executor = BulkheadExecutor()
        logger.info("BulkheadExecutor ready")
    
    return _executor


def shutdown_bulkhead_executor():
    """Shutdown global executor - called on container shutdown"""
    global _executor
    
    if _executor is not None:
        _executor.shutdown()
        _executor = None
