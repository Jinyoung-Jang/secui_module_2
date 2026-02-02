"""
System metrics collector using psutil.
"""

import time
import psutil
from typing import Dict, List, Any
from datetime import datetime


class MetricsCollector:
    """Collects system metrics using psutil."""

    def __init__(self, config):
        """
        Initialize the metrics collector.

        Args:
            config: Configuration object
        """
        self.config = config
        self.hostname = config.hostname

        # Store previous network/disk I/O counters for rate calculation
        self._prev_net_io = None
        self._prev_disk_io = None
        self._prev_time = None

    def collect_all(self) -> Dict[str, Any]:
        """
        Collect all enabled metrics.

        Returns:
            Dictionary containing all collected metrics
        """
        metrics = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'hostname': self.hostname,
            'metrics': {}
        }

        if self.config.is_metric_enabled('cpu'):
            metrics['metrics']['cpu'] = self.collect_cpu_metrics()

        if self.config.is_metric_enabled('memory'):
            metrics['metrics']['memory'] = self.collect_memory_metrics()

        if self.config.is_metric_enabled('disk'):
            metrics['metrics']['disk'] = self.collect_disk_metrics()

        if self.config.is_metric_enabled('network'):
            metrics['metrics']['network'] = self.collect_network_metrics()

        return metrics

    def collect_cpu_metrics(self) -> Dict[str, Any]:
        """
        Collect CPU metrics.

        Returns:
            Dictionary containing CPU metrics
        """
        metrics = {}

        # CPU percentages
        cpu_times = psutil.cpu_times_percent(interval=1)
        metrics['usage'] = {
            'total': psutil.cpu_percent(interval=None),
            'user': cpu_times.user,
            'system': cpu_times.system,
            'idle': cpu_times.idle,
        }

        # Add iowait if available (Linux)
        if hasattr(cpu_times, 'iowait'):
            metrics['usage']['iowait'] = cpu_times.iowait

        # Per-CPU metrics if enabled
        if self.config.get('metrics', 'cpu', 'per_cpu', default=True):
            per_cpu = psutil.cpu_percent(interval=None, percpu=True)
            metrics['cores'] = {
                'usage': per_cpu,
                'count': psutil.cpu_count(logical=True),
                'physical_count': psutil.cpu_count(logical=False)
            }

        # Load average (Unix-like systems)
        try:
            load_avg = psutil.getloadavg()
            metrics['load'] = {
                'average': {
                    '1m': load_avg[0],
                    '5m': load_avg[1],
                    '15m': load_avg[2]
                }
            }
        except (AttributeError, OSError):
            # Not available on Windows
            pass

        return metrics

    def collect_memory_metrics(self) -> Dict[str, Any]:
        """
        Collect memory metrics.

        Returns:
            Dictionary containing memory metrics
        """
        metrics = {}

        # Virtual memory
        vmem = psutil.virtual_memory()
        metrics['total'] = vmem.total
        metrics['used'] = vmem.used
        metrics['available'] = vmem.available
        metrics['free'] = vmem.free
        metrics['usage'] = {
            'percent': vmem.percent
        }

        # Add buffers and cached if available (Linux)
        if hasattr(vmem, 'buffers'):
            metrics['buffers'] = vmem.buffers
        if hasattr(vmem, 'cached'):
            metrics['cached'] = vmem.cached

        # Swap memory
        swap = psutil.swap_memory()
        metrics['swap'] = {
            'total': swap.total,
            'used': swap.used,
            'free': swap.free,
            'usage': {
                'percent': swap.percent
            }
        }

        return metrics

    def collect_disk_metrics(self) -> Dict[str, Any]:
        """
        Collect disk metrics.

        Returns:
            Dictionary containing disk metrics
        """
        metrics = {
            'partitions': [],
            'io': {}
        }

        # Get exclusion lists
        exclude_fs = self.config.get('metrics', 'disk', 'exclude_filesystems', default=[])
        exclude_mp = self.config.get('metrics', 'disk', 'exclude_mountpoints', default=[])

        # Disk usage per partition
        for partition in psutil.disk_partitions(all=False):
            # Skip excluded filesystems
            if partition.fstype in exclude_fs:
                continue

            # Skip excluded mountpoints
            if any(partition.mountpoint.startswith(pattern.rstrip('*'))
                   for pattern in exclude_mp):
                continue

            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partition_metrics = {
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'usage': {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    }
                }

                # Inode information (Unix-like systems)
                try:
                    import os
                    statvfs = os.statvfs(partition.mountpoint)
                    partition_metrics['inode'] = {
                        'total': statvfs.f_files,
                        'used': statvfs.f_files - statvfs.f_ffree,
                        'free': statvfs.f_ffree,
                        'usage': {
                            'percent': ((statvfs.f_files - statvfs.f_ffree) / statvfs.f_files * 100)
                                      if statvfs.f_files > 0 else 0
                        }
                    }
                except (AttributeError, OSError):
                    # Not available on Windows
                    pass

                metrics['partitions'].append(partition_metrics)
            except (PermissionError, OSError):
                # Skip partitions we can't access
                continue

        # Disk I/O statistics
        current_time = time.time()
        disk_io = psutil.disk_io_counters(perdisk=False)

        if disk_io:
            if self._prev_disk_io and self._prev_time:
                time_delta = current_time - self._prev_time
                if time_delta > 0:
                    metrics['io'] = {
                        'read': {
                            'bytes': (disk_io.read_bytes - self._prev_disk_io.read_bytes) / time_delta,
                            'count': (disk_io.read_count - self._prev_disk_io.read_count) / time_delta
                        },
                        'write': {
                            'bytes': (disk_io.write_bytes - self._prev_disk_io.write_bytes) / time_delta,
                            'count': (disk_io.write_count - self._prev_disk_io.write_count) / time_delta
                        }
                    }

            # Store current values for next iteration
            self._prev_disk_io = disk_io
            self._prev_time = current_time

        return metrics

    def collect_network_metrics(self) -> Dict[str, Any]:
        """
        Collect network metrics.

        Returns:
            Dictionary containing network metrics
        """
        metrics = {
            'interfaces': [],
            'connections': {}
        }

        # Get interface filters
        include_ifaces = self.config.get('metrics', 'network', 'interfaces', default=[])
        exclude_ifaces = self.config.get('metrics', 'network', 'exclude_interfaces', default=[])

        # Network I/O per interface
        current_time = time.time()
        net_io = psutil.net_io_counters(pernic=True)

        for iface, counters in net_io.items():
            # Filter interfaces
            if include_ifaces and iface not in include_ifaces:
                continue
            if iface in exclude_ifaces:
                continue

            iface_metrics = {
                'name': iface,
                'io': {
                    'bytes': {
                        'sent': counters.bytes_sent,
                        'recv': counters.bytes_recv
                    },
                    'packets': {
                        'sent': counters.packets_sent,
                        'recv': counters.packets_recv
                    },
                    'errors': {
                        'in': counters.errin,
                        'out': counters.errout
                    },
                    'dropped': {
                        'in': counters.dropin,
                        'out': counters.dropout
                    }
                }
            }

            # Calculate rates if we have previous data
            if self._prev_net_io and iface in self._prev_net_io and self._prev_time:
                time_delta = current_time - self._prev_time
                if time_delta > 0:
                    prev = self._prev_net_io[iface]
                    iface_metrics['io_rate'] = {
                        'bytes_sent': (counters.bytes_sent - prev.bytes_sent) / time_delta,
                        'bytes_recv': (counters.bytes_recv - prev.bytes_recv) / time_delta,
                        'packets_sent': (counters.packets_sent - prev.packets_sent) / time_delta,
                        'packets_recv': (counters.packets_recv - prev.packets_recv) / time_delta
                    }

            metrics['interfaces'].append(iface_metrics)

        # Store current values for next iteration
        self._prev_net_io = net_io
        self._prev_time = current_time

        # Network connections
        try:
            connections = psutil.net_connections(kind='inet')
            conn_stats = {
                'tcp': 0,
                'udp': 0,
                'established': 0,
                'time_wait': 0,
                'close_wait': 0,
                'listen': 0
            }

            for conn in connections:
                if conn.type == 1:  # SOCK_STREAM (TCP)
                    conn_stats['tcp'] += 1
                elif conn.type == 2:  # SOCK_DGRAM (UDP)
                    conn_stats['udp'] += 1

                if hasattr(conn, 'status'):
                    status = conn.status.lower()
                    if status == 'established':
                        conn_stats['established'] += 1
                    elif status == 'time_wait':
                        conn_stats['time_wait'] += 1
                    elif status == 'close_wait':
                        conn_stats['close_wait'] += 1
                    elif status == 'listen':
                        conn_stats['listen'] += 1

            metrics['connections'] = conn_stats
        except (psutil.AccessDenied, PermissionError):
            # May require elevated privileges
            pass

        return metrics
