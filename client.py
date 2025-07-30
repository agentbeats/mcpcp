import asyncio
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from fastmcp.server.auth.providers.bearer import RSAKeyPair
from pydantic import SecretStr
from mcpcp import access_control

MCPCP_URL = "http://0.0.0.0:9003/mcp/"


def generate_token(client_id: str, scopes: list = None):
    """Generate a test token for the given client_id and scopes"""
    if scopes is None:
        scopes = ["list_tools", "call_tools"]

    with open("mcp_auth/private.pem", "r") as f:
        private_key_pem = f.read()

    with open("mcp_auth/public.pem", "r") as f:
        public_key_pem = f.read()

    key_pair = RSAKeyPair(
        private_key=SecretStr(private_key_pem), public_key=public_key_pem
    )

    token = key_pair.create_token(
        subject=client_id,
        issuer="https://mcpcp",
        audience="mcpcp-server",
        scopes=scopes,
        expires_in_seconds=3600,  # 1 hour
    )
    return token


class AuthenticatedMCPClient:
    """MCP client that supports bearer token authentication using FastMCP"""

    def __init__(self, base_url: str, agent_name: str, scopes: list = None):
        self.base_url = base_url
        self.agent_name = agent_name
        self.scopes = scopes or ["list_tools", "call_tools"]
        self.token = generate_token(agent_name, self.scopes)

    async def list_tools(self):
        """List available tools using FastMCP client with bearer auth"""
        async with Client(
            self.base_url, auth=BearerAuth(token=self.token)
        ) as client:
            tools = await client.list_tools()
            return [{"name": tool.name} for tool in tools]

    async def call_tool(self, tool_name: str, arguments: dict = None):
        """Call a specific tool using FastMCP client with bearer auth"""
        if arguments is None:
            arguments = {}

        async with Client(
            self.base_url, auth=BearerAuth(token=self.token)
        ) as client:
            result = await client.call_tool(tool_name, arguments)
            return result


async def get_allowed_tools(agent_name):
    """Get tools allowed for a specific agent"""
    print(f"\n🔍 Getting tools for agent: {agent_name}")
    print(
        f"📋 Agent has access to servers: {access_control.get(agent_name, ['none'])}"
    )

    try:
        client = AuthenticatedMCPClient(MCPCP_URL, agent_name)

        tools = await client.list_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.get('name', 'unnamed')}")

        return tools

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return []


async def demo_different_agents():
    """Demonstrate how different agents see different tools"""
    print("=" * 60)
    print("🚀 MCPCP Client Authentication Demo")
    print("=" * 60)

    # Test each configured agent
    for agent_name in access_control.keys():
        print(f"🔍 Getting tools for agent: {agent_name}")
        await get_allowed_tools(agent_name)


async def main():
    """Main function - choose what to run"""
    await demo_different_agents()


if __name__ == "__main__":
    asyncio.run(main())
