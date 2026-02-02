"""
Unit tests for the metrics collector.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from metrics_collector import MetricsCollector


class MockConfig:
    """Mock configuration for testing."""

    def __init__(self):
        self.hostname = 'test-host'
        self._metrics = {
            'cpu': {'enabled': True, 'per_cpu': True},
            'memory': {'enabled': True},
            'disk': {'enabled': True, 'exclude_filesystems': [], 'exclude_mountpoints': []},
            'network': {'enabled': True, 'interfaces': [], 'exclude_interfaces': []}
        }

    def is_metric_enabled(self, metric_type: str) -> bool:
        return self._metrics.get(metric_type, {}).get('enabled', False)

    def get(self, *keys, default=None):
        value = self._metrics
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return default
            value = value[key]
        return value


@pytest.fixture
def config():
    """Create a mock configuration."""
    return MockConfig()


@pytest.fixture
def collector(config):
    """Create a metrics collector instance."""
    return MetricsCollector(config)


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_initialization(self, config):
        """Test collector initialization."""
        collector = MetricsCollector(config)
        assert collector.config == config
        assert collector.hostname == 'test-host'

    def test_collect_cpu_metrics(self, collector):
        """Test CPU metrics collection."""
        metrics = collector.collect_cpu_metrics()

        # Check required fields
        assert 'usage' in metrics
        assert 'total' in metrics['usage']
        assert 'user' in metrics['usage']
        assert 'system' in metrics['usage']
        assert 'idle' in metrics['usage']

        # Check CPU percentage values are valid
        assert 0 <= metrics['usage']['total'] <= 100
        assert 0 <= metrics['usage']['user'] <= 100
        assert 0 <= metrics['usage']['system'] <= 100
        assert 0 <= metrics['usage']['idle'] <= 100

        # Check per-CPU metrics
        if 'cores' in metrics:
            assert 'usage' in metrics['cores']
            assert 'count' in metrics['cores']
            assert isinstance(metrics['cores']['usage'], list)
            assert metrics['cores']['count'] > 0

    def test_collect_memory_metrics(self, collector):
        """Test memory metrics collection."""
        metrics = collector.collect_memory_metrics()

        # Check required fields
        assert 'total' in metrics
        assert 'used' in metrics
        assert 'available' in metrics
        assert 'free' in metrics
        assert 'usage' in metrics
        assert 'percent' in metrics['usage']

        # Check memory values are valid
        assert metrics['total'] > 0
        assert metrics['used'] >= 0
        assert metrics['available'] >= 0
        assert metrics['free'] >= 0
        assert 0 <= metrics['usage']['percent'] <= 100

        # Check swap memory
        assert 'swap' in metrics
        assert 'total' in metrics['swap']
        assert 'used' in metrics['swap']
        assert 'free' in metrics['swap']
        assert 'usage' in metrics['swap']

    def test_collect_disk_metrics(self, collector):
        """Test disk metrics collection."""
        metrics = collector.collect_disk_metrics()

        # Check structure
        assert 'partitions' in metrics
        assert 'io' in metrics
        assert isinstance(metrics['partitions'], list)

        # Check partition metrics (if any partitions exist)
        if metrics['partitions']:
            partition = metrics['partitions'][0]
            assert 'device' in partition
            assert 'mountpoint' in partition
            assert 'fstype' in partition
            assert 'usage' in partition
            assert 'total' in partition['usage']
            assert 'used' in partition['usage']
            assert 'free' in partition['usage']
            assert 'percent' in partition['usage']

            # Check values are valid
            assert partition['usage']['total'] > 0
            assert partition['usage']['used'] >= 0
            assert partition['usage']['free'] >= 0
            assert 0 <= partition['usage']['percent'] <= 100

    def test_collect_network_metrics(self, collector):
        """Test network metrics collection."""
        metrics = collector.collect_network_metrics()

        # Check structure
        assert 'interfaces' in metrics
        assert 'connections' in metrics
        assert isinstance(metrics['interfaces'], list)

        # Check interface metrics (if any interfaces exist)
        if metrics['interfaces']:
            interface = metrics['interfaces'][0]
            assert 'name' in interface
            assert 'io' in interface
            assert 'bytes' in interface['io']
            assert 'packets' in interface['io']
            assert 'errors' in interface['io']
            assert 'dropped' in interface['io']

            # Check values are valid (non-negative)
            assert interface['io']['bytes']['sent'] >= 0
            assert interface['io']['bytes']['recv'] >= 0
            assert interface['io']['packets']['sent'] >= 0
            assert interface['io']['packets']['recv'] >= 0

    def test_collect_all(self, collector):
        """Test collecting all metrics."""
        metrics = collector.collect_all()

        # Check top-level structure
        assert 'timestamp' in metrics
        assert 'hostname' in metrics
        assert 'metrics' in metrics
        assert metrics['hostname'] == 'test-host'

        # Check all metric types are present
        assert 'cpu' in metrics['metrics']
        assert 'memory' in metrics['metrics']
        assert 'disk' in metrics['metrics']
        assert 'network' in metrics['metrics']

        # Verify timestamp format (ISO 8601)
        assert 'T' in metrics['timestamp']
        assert metrics['timestamp'].endswith('Z')

    def test_collect_with_disabled_metrics(self, config):
        """Test collection with some metrics disabled."""
        # Disable disk and network metrics
        config._metrics['disk']['enabled'] = False
        config._metrics['network']['enabled'] = False

        collector = MetricsCollector(config)
        metrics = collector.collect_all()

        # Only CPU and memory should be present
        assert 'cpu' in metrics['metrics']
        assert 'memory' in metrics['metrics']
        assert 'disk' not in metrics['metrics']
        assert 'network' not in metrics['metrics']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
