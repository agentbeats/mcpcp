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


# Granular access control: agent_name -> {server_name: [tool_names]}
# Use "*" to grant access to all tools from a server
access_control = {
    "agent_name1": {
        "mcp1": ["update_battle_process"],  # Only specific tools from mcp1
        "mcp3": "*"  # All tools from mcp3
    },
    "agent_name2": {
        "mcp2": "*",  # All tools from mcp2
        "mcp3": ["run_python_code"]  # Only specific tools from mcp3
    },
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
            return []

        result = await call_next(context)
        allowed_access = access_control.get(caller_info, {})

        if not allowed_access:
            logger.warning(
                f"No access control found for caller: {caller_info}")
            return []

        # Filter tools by allowed servers and tools, remove server prefixes
        filtered_tools = []
        seen_tool_names = set()

        # Process tools in order of server priority
        for server, allowed_tools in allowed_access.items():
            for tool in result:
                # Check if tool belongs to this server (has server prefix)
                if tool.name.startswith(f"{server}_"):
                    # Remove server prefix to get clean tool name
                    clean_tool_name = tool.name[len(f"{server}_"):]

                    # Check if this specific tool is allowed
                    if allowed_tools == "*" or clean_tool_name in allowed_tools:
                        # Only add if we haven't seen this tool name before (handles conflicts)
                        if clean_tool_name not in seen_tool_names:
                            clean_tool = tool.copy()
                            clean_tool.name = clean_tool_name

                            filtered_tools.append(clean_tool)
                            seen_tool_names.add(clean_tool_name)
                            logger.info(
                                f"Added tool '{clean_tool_name}' from server '{server}' for {caller_info}")

        logger.info(
            f"Filtered tools for {caller_info}: {len(filtered_tools)} tools (from {len(result)}), removed server prefixes"
        )
        return filtered_tools


server.add_middleware(ListingFilterMiddleware())


class ToolCallFilterMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        print(context)
        logger.info(
            f"ToolCallFilterMiddleware: on_call_tool called for tool: {context.message.name}")

        try:
            # Access the token information
            access_token = get_access_token()
            caller_info = access_token.client_id
            logger.info(
                f"Tool call requested by: {caller_info} for tool: {context.message.name}")
        except Exception as e:
            logger.warning(
                f"No valid authentication token provided for call_tool request: {e}")
            raise Exception("Authentication required")

        allowed_access = access_control.get(caller_info, {})

        if not allowed_access:
            logger.warning(
                f"No access control found for caller: {caller_info}")
            raise Exception(f"Access denied for caller: {caller_info}")

        # Find the correct server for this tool based on access control priority
        for server, allowed_tools in allowed_access.items():
            # Check if this tool is allowed for this server
            if allowed_tools == "*" or context.message.name in allowed_tools:
                prefixed_tool_name = f"{server}_{context.message.name}"
                # Modify the context to use the prefixed tool name
                original_tool_name = context.message.name
                context.message.name = prefixed_tool_name

                try:
                    # Try to call with the prefixed name
                    result = await call_next(context)
                    logger.info(
                        f"Successfully called tool '{context.message.name}' on server '{server}' for {caller_info}")
                    return result
                except Exception as e:
                    logger.debug(
                        f"Tool '{prefixed_tool_name}' not found on server '{server}': {e}")
                    # Restore original name and try next server
                    context.message.name = original_tool_name
                    continue

        # If we get here, the tool wasn't found on any allowed server or access was denied
        logger.error(
            f"Tool '{context.message.name}' not found on any allowed servers or access denied for {caller_info}")
        raise Exception(
            f"Tool '{context.message.name}' not found or access denied")


server.add_middleware(ToolCallFilterMiddleware())


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
        transport="http", host="0.0.0.0", port=args.port, log_level="ERROR", stateless_http=True
    )
