"""
Main entry point for the metrics collector.
"""

import sys
import time
import signal
import logging
import argparse
from pathlib import Path
from typing import Optional

import schedule

from config import Config
from metrics_collector import MetricsCollector
from metrics_sender import MetricsSender


# Global flag for graceful shutdown
shutdown_flag = False


def setup_logging(config: Config):
    """
    Setup logging configuration.

    Args:
        config: Configuration object
    """
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    # Configure root logger
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # File handler if configured
    log_file = config.log_file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.get('logging', 'max_size', default=10) * 1024 * 1024,
            backupCount=config.get('logging', 'backup_count', default=3)
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers
    )


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_flag
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_flag = True


def collect_and_send(collector: MetricsCollector, sender: MetricsSender):
    """
    Collect metrics and send to API server.

    Args:
        collector: MetricsCollector instance
        sender: MetricsSender instance
    """
    logger = logging.getLogger(__name__)

    try:
        logger.debug("Collecting metrics...")
        metrics = collector.collect_all()

        logger.debug("Sending metrics...")
        success = sender.send(metrics)

        if success:
            logger.info("Metrics collected and sent successfully")
        else:
            logger.warning("Failed to send metrics (buffered for later)")

    except Exception as e:
        logger.error(f"Error collecting/sending metrics: {e}", exc_info=True)


def run_collector(config_path: Optional[str] = None):
    """
    Run the metrics collector.

    Args:
        config_path: Path to configuration file
    """
    global shutdown_flag

    # Load configuration
    config = Config(config_path)

    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("System Metrics Collector Starting")
    logger.info("=" * 60)
    logger.info(f"Hostname: {config.hostname}")
    logger.info(f"API Server: {config.server_url}")
    logger.info(f"Collection Interval: {config.collector_interval}s")
    logger.info(f"Buffer Directory: {config.buffer_dir}")

    # Log enabled metrics
    enabled_metrics = []
    for metric_type in ['cpu', 'memory', 'disk', 'network']:
        if config.is_metric_enabled(metric_type):
            enabled_metrics.append(metric_type)
    logger.info(f"Enabled Metrics: {', '.join(enabled_metrics)}")
    logger.info("=" * 60)

    # Initialize collector and sender
    collector = MetricsCollector(config)
    sender = MetricsSender(config)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Schedule metric collection
    interval = config.collector_interval
    schedule.every(interval).seconds.do(
        collect_and_send,
        collector=collector,
        sender=sender
    )

    # Collect immediately on start
    logger.info("Collecting initial metrics...")
    collect_and_send(collector, sender)

    # Main loop
    logger.info("Entering main collection loop")
    while not shutdown_flag:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(5)

    # Shutdown
    logger.info("Shutting down collector...")

    # Log buffer statistics
    buffer_stats = sender.get_buffer_stats()
    logger.info(f"Buffer stats: {buffer_stats['count']} files, "
                f"{buffer_stats['total_size'] / 1024:.2f} KB "
                f"({buffer_stats['usage_percent']:.1f}% of max)")

    logger.info("Collector stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='System Metrics Collector',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-c', '--config',
        type=str,
        default=None,
        help='Path to configuration file (default: config/collector-config.yaml)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    args = parser.parse_args()

    try:
        run_collector(args.config)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
