# MCPCP

## Overview

MCPCP consists of multiple MCP servers and a central proxy server that provides authentication, access control, and unified access to distributed tools and resources.

### Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │───▶│  Proxy Server   │
└─────────────────┘    │   (port 9003)   │
                       └─────────┬───────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌────▼────┐ ┌────▼────┐
              │  MCP1     │ │  MCP2   │ │  MCP3   │
              │(port 9004)│ │(port 9005)│(port 9006)│
              └───────────┘ └─────────┘ └─────────┘
```

## Components

### MCP Servers
- **mcp1.py** (port 9004): Battle process logging and result reporting
- **mcp2.py** (port 9005): Docker command execution
- **mcp3.py** (port 9006): Python code execution

### Proxy Server
- **mcpcp.py** (port 9003): Authentication, access control, and request routing

### Launcher
- **launch_servers.py**: Automated startup and monitoring of all servers

## Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Authentication Keys

(This is for PoC only)

```bash
python mcp_auth/generate_keys.py
```

This creates:
- `mcp_auth/private.pem` - Private key for signing tokens
- `mcp_auth/public.pem` - Public key for verifying tokens

### 3. Launch All Servers

```bash
python launch_servers.py
```

This will:
1. Start all 3 MCP servers (ports 9004-9006)
2. Wait for initialization
3. Start the proxy server (port 9003)
4. Monitor all processes

### 4. Stop Servers

Press `Ctrl+C` to gracefully shutdown all servers.

## Development

### Project Structure

```
mcpcp/
├── mcp_servers/          # Individual MCP servers
│   ├── mcp1.py           # Example MCP Server 1
│   ├── mcp2.py           # Example MCP Server 2
│   └── mcp3.py           # Example MCP Server 3
├── mcp_auth/             # Authentication utilities
│   └── generate_keys.py  # RSA key generation
├── mcpcp.py              # Main MCPCP proxy server
├── launch_servers.py     # Server launcher and monitor
├── client.py             # Example client
└── README.md             # This file
```
