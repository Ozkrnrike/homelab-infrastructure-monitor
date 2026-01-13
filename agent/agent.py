#!/usr/bin/env python3
"""
HomeLab Infrastructure Monitor - Collection Agent
Collects system metrics and sends them to the central monitoring server.
"""

import sys
import time
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

import psutil
import requests
import yaml
from pydantic import BaseModel, Field, ValidationError


# Configuration Models
class ServerConfig(BaseModel):
    url: str
    api_key: str


class CollectionConfig(BaseModel):
    interval_seconds: int = Field(default=30, ge=5, le=3600)
    include_docker: bool = True
    disk_mounts: List[str] = Field(default_factory=lambda: ["/"])


class HealthCheckConfig(BaseModel):
    name: str
    type: str  # http, tcp, process
    url: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    expected_status: Optional[int] = 200


class AgentConfig(BaseModel):
    server: ServerConfig
    collection: CollectionConfig = Field(default_factory=CollectionConfig)
    health_checks: List[HealthCheckConfig] = Field(default_factory=list)


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects system metrics using psutil."""

    def __init__(self, config: CollectionConfig):
        self.config = config
        self.last_disk_io = None
        self.last_net_io = None
        self.last_time = None

    def collect_cpu_metrics(self) -> Dict[str, Any]:
        """Collect CPU usage metrics."""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]

        return {
            "percent": cpu_percent,
            "load_avg": list(load_avg),
            "count": psutil.cpu_count(logical=True)
        }

    def collect_memory_metrics(self) -> Dict[str, Any]:
        """Collect memory usage metrics."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "total": mem.total,
            "used": mem.used,
            "available": mem.available,
            "percent": mem.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_percent": swap.percent
        }

    def collect_disk_metrics(self) -> List[Dict[str, Any]]:
        """Collect disk usage metrics."""
        disks = []

        for mount in self.config.disk_mounts:
            try:
                usage = psutil.disk_usage(mount)
                disks.append({
                    "mount": mount,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                })
            except Exception as e:
                logger.warning(f"Failed to get disk usage for {mount}: {e}")

        return disks

    def collect_disk_io_metrics(self) -> Dict[str, Any]:
        """Collect disk I/O metrics with rates."""
        current_io = psutil.disk_io_counters()
        current_time = time.time()

        if self.last_disk_io is None or self.last_time is None:
            self.last_disk_io = current_io
            self.last_time = current_time
            return {
                "read_bytes": 0,
                "write_bytes": 0,
                "read_bytes_per_sec": 0,
                "write_bytes_per_sec": 0
            }

        time_delta = current_time - self.last_time
        read_rate = (current_io.read_bytes - self.last_disk_io.read_bytes) / time_delta
        write_rate = (current_io.write_bytes - self.last_disk_io.write_bytes) / time_delta

        self.last_disk_io = current_io
        self.last_time = current_time

        return {
            "read_bytes": current_io.read_bytes,
            "write_bytes": current_io.write_bytes,
            "read_bytes_per_sec": int(read_rate),
            "write_bytes_per_sec": int(write_rate)
        }

    def collect_network_metrics(self) -> Dict[str, Any]:
        """Collect network I/O metrics with rates."""
        current_net = psutil.net_io_counters()
        current_time = time.time()

        if self.last_net_io is None or self.last_time is None:
            self.last_net_io = current_net
            self.last_time = current_time
            return {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "bytes_sent_per_sec": 0,
                "bytes_recv_per_sec": 0
            }

        time_delta = current_time - self.last_time
        send_rate = (current_net.bytes_sent - self.last_net_io.bytes_sent) / time_delta
        recv_rate = (current_net.bytes_recv - self.last_net_io.bytes_recv) / time_delta

        self.last_net_io = current_net

        return {
            "bytes_sent": current_net.bytes_sent,
            "bytes_recv": current_net.bytes_recv,
            "bytes_sent_per_sec": int(send_rate),
            "bytes_recv_per_sec": int(recv_rate)
        }

    def collect_system_info(self) -> Dict[str, Any]:
        """Collect general system information."""
        boot_time = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time)

        return {
            "hostname": psutil.hostname() if hasattr(psutil, 'hostname') else "unknown",
            "boot_time": datetime.fromtimestamp(boot_time, tz=timezone.utc).isoformat(),
            "uptime_seconds": uptime_seconds
        }

    def collect_docker_metrics(self) -> List[Dict[str, Any]]:
        """Collect Docker container metrics if Docker is available."""
        if not self.config.include_docker:
            return []

        try:
            import docker
            client = docker.from_env()
            containers = []

            for container in client.containers.list(all=True):
                try:
                    stats = container.stats(stream=False) if container.status == 'running' else {}

                    container_info = {
                        "id": container.id[:12],
                        "name": container.name,
                        "image": container.image.tags[0] if container.image.tags else "unknown",
                        "status": container.status,
                        "created": container.attrs['Created'],
                    }

                    if container.status == 'running' and stats:
                        # Calculate CPU percentage
                        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                                   stats['precpu_stats']['cpu_usage']['total_usage']
                        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                      stats['precpu_stats']['system_cpu_usage']
                        cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0

                        # Memory usage
                        mem_usage = stats['memory_stats'].get('usage', 0)
                        mem_limit = stats['memory_stats'].get('limit', 1)
                        mem_percent = (mem_usage / mem_limit) * 100.0 if mem_limit > 0 else 0

                        container_info.update({
                            "cpu_percent": round(cpu_percent, 2),
                            "memory_usage": mem_usage,
                            "memory_percent": round(mem_percent, 2),
                            "network_rx_bytes": stats['networks'].get('eth0', {}).get('rx_bytes', 0),
                            "network_tx_bytes": stats['networks'].get('eth0', {}).get('tx_bytes', 0),
                        })

                    containers.append(container_info)
                except Exception as e:
                    logger.warning(f"Failed to get stats for container {container.name}: {e}")

            return containers
        except ImportError:
            logger.warning("Docker library not installed, skipping Docker metrics")
            return []
        except Exception as e:
            logger.warning(f"Failed to collect Docker metrics: {e}")
            return []

    def collect_all(self) -> Dict[str, Any]:
        """Collect all metrics."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": self.collect_system_info(),
            "metrics": {
                "cpu": self.collect_cpu_metrics(),
                "memory": self.collect_memory_metrics(),
                "disks": self.collect_disk_metrics(),
                "disk_io": self.collect_disk_io_metrics(),
                "network": self.collect_network_metrics()
            },
            "containers": self.collect_docker_metrics()
        }


class HealthChecker:
    """Performs health checks on services."""

    @staticmethod
    def check_http(config: HealthCheckConfig) -> Dict[str, Any]:
        """Check HTTP/HTTPS endpoint."""
        try:
            start_time = time.time()
            response = requests.get(config.url, timeout=5)
            response_time = time.time() - start_time

            is_healthy = response.status_code == config.expected_status

            return {
                "name": config.name,
                "type": "http",
                "healthy": is_healthy,
                "status_code": response.status_code,
                "response_time_ms": int(response_time * 1000),
                "message": "OK" if is_healthy else f"Expected {config.expected_status}, got {response.status_code}"
            }
        except Exception as e:
            return {
                "name": config.name,
                "type": "http",
                "healthy": False,
                "message": str(e)
            }

    @staticmethod
    def check_tcp(config: HealthCheckConfig) -> Dict[str, Any]:
        """Check TCP port connectivity."""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((config.host, config.port))
            sock.close()

            is_healthy = result == 0

            return {
                "name": config.name,
                "type": "tcp",
                "healthy": is_healthy,
                "host": config.host,
                "port": config.port,
                "message": "Port is open" if is_healthy else "Port is closed"
            }
        except Exception as e:
            return {
                "name": config.name,
                "type": "tcp",
                "healthy": False,
                "message": str(e)
            }

    @staticmethod
    def check_all(health_checks: List[HealthCheckConfig]) -> List[Dict[str, Any]]:
        """Run all configured health checks."""
        results = []

        for check in health_checks:
            if check.type == "http":
                results.append(HealthChecker.check_http(check))
            elif check.type == "tcp":
                results.append(HealthChecker.check_tcp(check))

        return results


class Agent:
    """Main agent class that coordinates collection and transmission."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.collector = MetricsCollector(self.config.collection)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.server.api_key}",
            "Content-Type": "application/json"
        })

        logger.info("Agent initialized successfully")

    @staticmethod
    def load_config(config_path: str) -> AgentConfig:
        """Load and validate configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)

            # Handle environment variable substitution
            if 'server' in config_dict and 'api_key' in config_dict['server']:
                import os
                api_key = config_dict['server']['api_key']
                if api_key.startswith('${') and api_key.endswith('}'):
                    env_var = api_key[2:-1]
                    config_dict['server']['api_key'] = os.getenv(env_var, '')

            return AgentConfig(**config_dict)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def send_metrics(self, payload: Dict[str, Any]) -> bool:
        """Send metrics to the backend server."""
        try:
            response = self.session.post(
                f"{self.config.server.url}/metrics",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Metrics sent successfully (status: {response.status_code})")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send metrics: {e}")
            return False

    def run(self):
        """Main agent loop."""
        logger.info(f"Starting agent loop (interval: {self.config.collection.interval_seconds}s)")

        while True:
            try:
                # Collect all metrics
                metrics = self.collector.collect_all()

                # Run health checks
                health_checks = HealthChecker.check_all(self.config.health_checks)
                if health_checks:
                    metrics["health_checks"] = health_checks

                # Send to server
                self.send_metrics(metrics)

                # Wait for next interval
                time.sleep(self.config.collection.interval_seconds)

            except KeyboardInterrupt:
                logger.info("Agent stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in agent loop: {e}", exc_info=True)
                time.sleep(self.config.collection.interval_seconds)


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="HomeLab Infrastructure Monitor Agent")
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    agent = Agent(config_path=args.config)
    agent.run()


if __name__ == "__main__":
    main()
