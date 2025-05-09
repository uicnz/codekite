#!/usr/bin/env python
"""
Script to explore the FastMCP client API.

This script will create a client and print its available attributes and methods.
"""

import asyncio
from fastmcp import Client

async def explore_client_api():
    """Explore the FastMCP client API."""
    print("[INFO] Creating FastMCP client...")
    client = Client("http://localhost:8000/mcp")

    # Print client attributes and methods
    print("\n[INFO] Client attributes and methods:")
    for attr in dir(client):
        if not attr.startswith('_'):  # Skip private attributes
            print(f"  - {attr}")

    try:
        # Try to get all tools
        print("\n[INFO] Available tools:")
        tools = await client.list_tools()
        for tool in tools:
            print(f"  - {tool.name}: {tool.description.split('.')[0]}")
    except Exception as e:
        print(f"[ERROR] Could not list tools: {e}")

    try:
        # Try to get all resources
        print("\n[INFO] Available resources:")
        resources = await client.list_resources()
        for resource in resources:
            print(f"  - {resource.name}: {resource.description.split('.')[0]}")
    except Exception as e:
        print(f"[ERROR] Could not list resources: {e}")

if __name__ == "__main__":
    asyncio.run(explore_client_api())
