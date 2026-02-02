"""
Metrics sender for transmitting collected metrics to the API server.
"""

import json
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


logger = logging.getLogger(__name__)


class MetricsSender:
    """Sends metrics to the API server with local buffering."""

    def __init__(self, config):
        """
        Initialize the metrics sender.

        Args:
            config: Configuration object
        """
        self.config = config
        self.server_url = config.server_url.rstrip('/') + '/api/v1/metrics/collect'
        self.api_key = config.api_key
        self.buffer_dir = config.buffer_dir
        self.buffer_max_size = config.buffer_max_size * 1024 * 1024  # Convert to bytes

        # Create buffer directory if it doesn't exist
        self.buffer_dir.mkdir(parents=True, exist_ok=True)

        # Timeout for HTTP requests (seconds)
        self.timeout = 10

    def send(self, metrics: Dict[str, Any]) -> bool:
        """
        Send metrics to the API server.

        Args:
            metrics: Metrics data to send

        Returns:
            True if successfully sent, False otherwise
        """
        # Try to send buffered metrics first
        self._send_buffered_metrics()

        # Try to send current metrics
        success = self._send_to_api(metrics)

        if not success:
            # Buffer the metrics if sending failed
            self._buffer_metrics(metrics)

        return success

    def _send_to_api(self, metrics: Dict[str, Any]) -> bool:
        """
        Send metrics to the API server via HTTP POST.

        Args:
            metrics: Metrics data to send

        Returns:
            True if successfully sent, False otherwise
        """
        try:
            headers = {
                'Content-Type': 'application/json'
            }

            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = requests.post(
                self.server_url,
                json=metrics,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.debug(f"Successfully sent metrics to {self.server_url}")
                return True
            else:
                logger.warning(
                    f"Failed to send metrics: HTTP {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout sending metrics to {self.server_url}")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error sending metrics to {self.server_url}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending metrics: {e}")
            return False

    def _buffer_metrics(self, metrics: Dict[str, Any]):
        """
        Save metrics to local buffer for later transmission.

        Args:
            metrics: Metrics data to buffer
        """
        # Check buffer size before adding
        current_size = self._get_buffer_size()
        if current_size >= self.buffer_max_size:
            logger.warning("Buffer is full, dropping oldest metrics")
            self._cleanup_old_buffers()

        # Create buffer file with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
        buffer_file = self.buffer_dir / f"metrics_{timestamp}.json"

        try:
            with open(buffer_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f)
            logger.info(f"Metrics buffered to {buffer_file}")
        except Exception as e:
            logger.error(f"Failed to buffer metrics: {e}")

    def _send_buffered_metrics(self):
        """Try to send all buffered metrics."""
        buffer_files = sorted(self.buffer_dir.glob('metrics_*.json'))

        if not buffer_files:
            return

        logger.info(f"Found {len(buffer_files)} buffered metric files")

        for buffer_file in buffer_files:
            try:
                with open(buffer_file, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)

                if self._send_to_api(metrics):
                    # Successfully sent, delete the buffer file
                    buffer_file.unlink()
                    logger.info(f"Sent buffered metrics from {buffer_file}")
                else:
                    # Failed to send, stop trying (server probably still down)
                    break

            except Exception as e:
                logger.error(f"Error processing buffer file {buffer_file}: {e}")
                # Delete corrupted buffer file
                buffer_file.unlink()

    def _get_buffer_size(self) -> int:
        """
        Get total size of buffered metrics.

        Returns:
            Total size in bytes
        """
        total_size = 0
        for buffer_file in self.buffer_dir.glob('metrics_*.json'):
            try:
                total_size += buffer_file.stat().st_size
            except OSError:
                pass
        return total_size

    def _cleanup_old_buffers(self):
        """Remove oldest buffered metrics to free up space."""
        buffer_files = sorted(self.buffer_dir.glob('metrics_*.json'))

        # Remove oldest 20% of files
        num_to_remove = max(1, len(buffer_files) // 5)

        for buffer_file in buffer_files[:num_to_remove]:
            try:
                buffer_file.unlink()
                logger.info(f"Removed old buffer file {buffer_file}")
            except OSError as e:
                logger.error(f"Failed to remove buffer file {buffer_file}: {e}")

    def get_buffer_stats(self) -> Dict[str, Any]:
        """
        Get statistics about buffered metrics.

        Returns:
            Dictionary with buffer statistics
        """
        buffer_files = list(self.buffer_dir.glob('metrics_*.json'))
        total_size = self._get_buffer_size()

        return {
            'count': len(buffer_files),
            'total_size': total_size,
            'max_size': self.buffer_max_size,
            'usage_percent': (total_size / self.buffer_max_size * 100) if self.buffer_max_size > 0 else 0
        }
