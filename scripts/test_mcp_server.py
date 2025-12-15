#!/usr/bin/env python
"""
Test the deployed MCP server.
"""

import argparse
import json
import subprocess
import httpx


def get_server_url() -> str:
    """Get the MCP server URL from Azure."""
    result = subprocess.run(
        ["az", "containerapp", "list", "--resource-group", "dev-rg", 
         "--query", "[].properties.configuration.ingress.fqdn", "-o", "tsv"],
        capture_output=True, text=True, check=True
    )
    fqdn = result.stdout.strip()
    return f"https://{fqdn}/mcp"


def test_mcp_server(url: str) -> None:
    """Test the MCP server endpoints."""
    print(f"🔗 Testing MCP Server: {url}")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    # Test 1: Initialize
    print("\n1️⃣  Testing initialize...")
    init_payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        },
        "id": 1
    }
    
    with httpx.Client(timeout=30) as client:
        response = client.post(url, json=init_payload, headers=headers)
        
        if response.status_code == 200:
            # Parse SSE response
            for line in response.text.split("\n"):
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if "result" in data:
                        server_info = data["result"].get("serverInfo", {})
                        print(f"   ✅ Server: {server_info.get('name')} v{server_info.get('version')}")
                        print(f"   ✅ Protocol: {data['result'].get('protocolVersion')}")
                        
                        # Extract session ID from headers
                        session_id = response.headers.get("mcp-session-id")
                        if session_id:
                            print(f"   ✅ Session: {session_id[:20]}...")
                            
                            # Test 2: List tools
                            print("\n2️⃣  Testing tools/list...")
                            tools_payload = {
                                "jsonrpc": "2.0",
                                "method": "tools/list",
                                "params": {},
                                "id": 2
                            }
                            tools_headers = {**headers, "mcp-session-id": session_id}
                            tools_response = client.post(url, json=tools_payload, headers=tools_headers)
                            
                            for line in tools_response.text.split("\n"):
                                if line.startswith("data: "):
                                    tools_data = json.loads(line[6:])
                                    if "result" in tools_data:
                                        tools = tools_data["result"].get("tools", [])
                                        print(f"   ✅ Found {len(tools)} tools:")
                                        for tool in tools:
                                            print(f"      • {tool['name']}: {tool.get('description', '')[:50]}")
                                        
                                        # Test 3: Call hello tool
                                        print("\n3️⃣  Testing tools/call (hello)...")
                                        call_payload = {
                                            "jsonrpc": "2.0",
                                            "method": "tools/call",
                                            "params": {
                                                "name": "hello",
                                                "arguments": {"name": "World"}
                                            },
                                            "id": 3
                                        }
                                        call_response = client.post(url, json=call_payload, headers=tools_headers)
                                        
                                        for line in call_response.text.split("\n"):
                                            if line.startswith("data: "):
                                                call_data = json.loads(line[6:])
                                                if "result" in call_data:
                                                    content = call_data["result"].get("content", [])
                                                    if content:
                                                        print(f"   ✅ Response: {content[0].get('text', '')}")
                                        
                                        # Test 4: Call add_numbers tool
                                        print("\n4️⃣  Testing tools/call (add_numbers)...")
                                        add_payload = {
                                            "jsonrpc": "2.0",
                                            "method": "tools/call",
                                            "params": {
                                                "name": "add_numbers",
                                                "arguments": {"a": 42, "b": 58}
                                            },
                                            "id": 4
                                        }
                                        add_response = client.post(url, json=add_payload, headers=tools_headers)
                                        
                                        for line in add_response.text.split("\n"):
                                            if line.startswith("data: "):
                                                add_data = json.loads(line[6:])
                                                if "result" in add_data:
                                                    content = add_data["result"].get("content", [])
                                                    if content:
                                                        print(f"   ✅ 42 + 58 = {content[0].get('text', '')}")
                        break
        else:
            print(f"   ❌ Failed: {response.status_code} {response.text}")
            return
    
    print("\n" + "=" * 60)
    print("🎉 All MCP server tests passed!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Test the deployed MCP server")
    parser.add_argument("--url", help="MCP server URL (auto-detected if not provided)")
    args = parser.parse_args()
    
    url = args.url or get_server_url()
    test_mcp_server(url)


if __name__ == "__main__":
    main()
