import asyncio
from fastmcp.server.auth.providers.bearer import RSAKeyPair
from pydantic import SecretStr
from mcpcp import access_control
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

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


async def get_allowed_tools(agent_name):
    """Get tools allowed for a specific agent"""
    print(f"\n🔍 Getting tools for agent: {agent_name}")
    print(
        f"📋 Agent has access to servers: {access_control.get(agent_name, ['none'])}"
    )

    token = generate_token(agent_name, ["list_tools", "call_tools"])
    try:
        async with streamablehttp_client(
            MCPCP_URL,
            {"Authorization": f"Bearer {token}"},
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
        print(f"✅ Found {len(tools.tools)} tools:")
        for tool in tools.tools:
            print(f"   - {tool.name}")

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
        token = generate_token(agent_name, ["list_tools", "call_tools"])
        async with streamablehttp_client(
            MCPCP_URL,
            {"Authorization": f"Bearer {token}"},
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("echo", {"message": "test"})
                print(f"✅ Result from echo tool: {result}\n")


async def main():
    """Main function - choose what to run"""
    await demo_different_agents()


if __name__ == "__main__":
    asyncio.run(main())
