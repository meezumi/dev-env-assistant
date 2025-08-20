#!/usr/bin/env python3
"""
Check MCP version and available imports
"""


def check_mcp_version():
    try:
        import mcp

        print(f"MCP version: {mcp.__version__}")
    except ImportError:
        print("MCP not installed")
        return False
    except AttributeError:
        print("MCP installed but version not available")

    # Check what's available in mcp.server.models
    try:
        from mcp.server import models

        print(f"Available in mcp.server.models: {dir(models)}")
    except ImportError as e:
        print(f"Cannot import mcp.server.models: {e}")

    # Check what's available in mcp.types
    try:
        import mcp.types as types

        print(f"Available in mcp.types: {dir(types)}")
    except ImportError as e:
        print(f"Cannot import mcp.types: {e}")

    # Check server availability
    try:
        from mcp.server import Server

        print("Server import: OK")
    except ImportError as e:
        print(f"Cannot import Server: {e}")

    return True


if __name__ == "__main__":
    check_mcp_version()
