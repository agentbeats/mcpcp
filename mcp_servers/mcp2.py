# -*- coding: utf-8 -*-
import logging
import os
import argparse
from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

server = FastMCP("Open MCP for AgentBeast Battle Arena")

SESSIONS: dict[str, dict[str, str]] = {}

BACKEND_URL = "http://localhost:9000"


@server.tool()
def echo(message: str) -> str:
    return f"Echo: {message}"


@server.tool()
def run_docker(command: str) -> str:
    return f"Docker: {command}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MCP Server 2 - AgentBeast Battle Arena"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", 9011)),
        help="Port to run the server on (default: %(default)s)",
    )

    args = parser.parse_args()

    logger.info(f"Starting MCP Server 2 on port {args.port}")
    server.run(
        transport="http", host="0.0.0.0", port=args.port, log_level="ERROR"
    )
