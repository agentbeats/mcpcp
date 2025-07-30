#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launch all MCP servers in the mcp_servers directory using subprocess.
"""

import os
import sys
import subprocess
import signal
import time
import logging
from pathlib import Path
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class ServerLauncher:
    def __init__(
        self,
        servers_dir: str = "mcp_servers",
        base_port: int = 9004,
        proxy_port: int = 9003,
    ):
        self.servers_dir = Path(servers_dir)
        self.base_port = base_port
        self.proxy_port = proxy_port
        self.processes: List[subprocess.Popen] = []
        self.server_info: Dict[str, Dict] = {}

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("Shutting down servers...")
        self.shutdown_all()
        sys.exit(0)

    def discover_servers(self) -> List[Path]:
        """Discover all Python files in the servers directory."""
        if not self.servers_dir.exists():
            logger.error(
                f"Servers directory '{self.servers_dir}' does not exist"
            )
            return []

        python_files = list(self.servers_dir.glob("*.py"))
        logger.info(f"Found {len(python_files)} MCP servers")
        return python_files

    def launch_server(self, server_file: Path, port: int) -> subprocess.Popen:
        """Launch a single server with the specified port."""
        try:
            # Use virtual environment Python interpreter
            venv_python = Path("venv/bin/python")
            if not venv_python.exists():
                logger.error("Virtual environment not found")
                return None

            # Launch the server
            cmd = [str(venv_python), str(server_file), "--port", str(port)]
            logger.info(f"Starting {server_file.name} on port {port}")

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Store server information
            self.server_info[server_file.name] = {
                "port": port,
                "process": process,
                "pid": process.pid,
            }

            return process

        except Exception as e:
            logger.error(f"Failed to launch {server_file.name}: {e}")
            return None

    def launch_all(self) -> bool:
        """Launch all discovered servers and the proxy server."""
        servers = self.discover_servers()

        if not servers:
            logger.warning("No servers found")
            return False

        # Launch MCP servers
        for i, server_file in enumerate(servers):
            port = self.base_port + i
            process = self.launch_server(server_file, port)

            if process:
                self.processes.append(process)
                time.sleep(0.5)

        # Wait for MCP servers to initialize
        if self.processes:
            logger.info("Waiting for MCP servers to initialize...")
            time.sleep(2)

            # Launch proxy server
            proxy_file = Path("mcpcp.py")
            if proxy_file.exists():
                logger.info("Starting proxy server...")
                proxy_process = self.launch_server(proxy_file, self.proxy_port)

                if proxy_process:
                    self.processes.append(proxy_process)
                    time.sleep(0.5)

        if self.processes:
            logger.info(f"Successfully launched {len(self.processes)} servers")
            self.print_status()
            return True
        else:
            logger.error("Failed to launch servers")
            return False

    def print_status(self):
        """Print server status."""
        logger.info("=" * 50)
        for server_name, info in self.server_info.items():
            status = "RUNNING" if info["process"].poll() is None else "STOPPED"
            logger.info(
                f"{server_name:<12} | Port: {info['port']:<4} | PID: {info['pid']:<6} | {status}"
            )
        logger.info("=" * 50)

    def monitor_servers(self):
        """Monitor running servers."""
        logger.info("Monitoring servers... Press Ctrl+C to stop")

        try:
            while True:
                # Check for stopped processes
                for process in self.processes[:]:
                    if process.poll() is not None:
                        # Find and log stopped server
                        for server_name, info in self.server_info.items():
                            if info["process"] == process:
                                logger.warning(f"{server_name} stopped")
                                # Show error if available
                                try:
                                    _, stderr = process.communicate(timeout=1)
                                    if stderr:
                                        logger.error(
                                            f"{server_name} error: {stderr.strip()}"
                                        )
                                except:
                                    pass
                                break
                        self.processes.remove(process)

                if not self.processes:
                    logger.error("All servers stopped")
                    break

                time.sleep(2)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")

    def shutdown_all(self):
        """Shutdown all servers."""
        if not self.processes:
            return

        logger.info("Shutting down servers...")

        # Terminate processes
        for server_name, info in self.server_info.items():
            process = info["process"]
            if process.poll() is None:
                try:
                    process.terminate()
                except:
                    pass

        # Wait and force kill if needed
        time.sleep(2)
        for server_name, info in self.server_info.items():
            process = info["process"]
            if process.poll() is None:
                try:
                    process.kill()
                except:
                    pass

        self.processes.clear()
        self.server_info.clear()
        logger.info("All servers shutdown")


def main():
    """Main entry point."""
    launcher = ServerLauncher()

    if launcher.launch_all():
        launcher.monitor_servers()

    launcher.shutdown_all()


if __name__ == "__main__":
    main()
