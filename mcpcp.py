import logging
import argparse
from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.auth import BearerAuthProvider
from fastmcp.server.dependencies import get_access_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Load public key for server authentication
with open("mcp_auth/public.pem", "r") as f:
    public_key = f.read()

auth = BearerAuthProvider(
    public_key=public_key, issuer="https://mcpcp", audience="mcpcp-server"
)


access_control = {
    "agent_name1": ["mcp1", "mcp3"],
    "agent_name2": ["mcp2", "mcp3"],
}


server_configs = {
    "mcp1": {
        "url": "http://0.0.0.0:9004/mcp/",
    },
    "mcp2": {
        "url": "http://0.0.0.0:9005/mcp/",
    },
    "mcp3": {
        "url": "http://0.0.0.0:9006/mcp/",
    },
}

server = FastMCP.as_proxy(
    server_configs,
    name="MCPCP",
    auth=auth,  # Add authentication to the server
)


class ListingFilterMiddleware(Middleware):
    async def on_list_tools(self, context: MiddlewareContext, call_next):
        logger.info("ListingFilterMiddleware: on_list_tools called")

        try:
            # Access the token information
            access_token = get_access_token()
            caller_info = access_token.client_id
            caller_scopes = access_token.scopes
            logger.info(
                f"Tools listing requested by: {caller_info} with scopes: {caller_scopes}"
            )
        except Exception as e:
            logger.warning(
                f"No valid authentication token provided for list_tools request: {e}"
            )
        result = await call_next(context)

        allowed_servers = access_control[caller_info]
        filtered_tools = [
            tool
            for tool in result
            if any(server in tool.name for server in allowed_servers)
        ]
        logger.info(
            f"Filtered tools for {caller_info}: {len(filtered_tools)} tools (from {len(result)})"
        )
        return filtered_tools

        return []


server.add_middleware(ListingFilterMiddleware())


def add_mcp_server(server_name, server_url):
    logger.info(f"Adding MCP server: {server_name} at {server_url}")
    server_configs[server_name] = {
        "url": server_url,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MCPCP Proxy Server - AgentBeast Battle Arena"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9003,
        help="Port to run the proxy server on (default: %(default)s)",
    )

    args = parser.parse_args()

    logger.info(f"Starting MCPCP Proxy Server on port {args.port}")
    server.run(
        transport="http", host="0.0.0.0", port=args.port, log_level="ERROR"
    )
