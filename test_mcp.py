#!/usr/bin/env python3
"""Test script for DavidOS MCP protocol endpoints."""

import requests
import json
import sys

BASE_URL = "https://davidos-mcp-production.up.railway.app"

def test_with_session(session_cookie=None):
    """Test MCP endpoints with an authenticated session."""
    
    headers = {
        "Content-Type": "application/json"
    }
    
    cookies = {}
    if session_cookie:
        cookies["session"] = session_cookie
    
    print("Testing MCP Protocol Endpoints\n")
    print("=" * 60)
    
    # Test 1: List Tools
    print("\n1. Testing list_tools...")
    response = requests.post(
        f"{BASE_URL}/mcp",
        headers=headers,
        cookies=cookies,
        json={"method": "list_tools", "params": {}}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data.get('tools', []))} tools:")
        for tool in data.get('tools', []):
            print(f"  - {tool['name']}: {tool['description']}")
    else:
        print(f"Error: {response.text}")
    
    # Test 2: List Resources
    print("\n2. Testing list_resources...")
    response = requests.post(
        f"{BASE_URL}/mcp",
        headers=headers,
        cookies=cookies,
        json={"method": "list_resources", "params": {}}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data.get('resources', []))} resources:")
        for resource in data.get('resources', []):
            print(f"  - {resource['uri']}: {resource['name']}")
    else:
        print(f"Error: {response.text}")
    
    # Test 3: Call get_context tool
    print("\n3. Testing call_tool (get_context)...")
    response = requests.post(
        f"{BASE_URL}/mcp",
        headers=headers,
        cookies=cookies,
        json={
            "method": "call_tool",
            "params": {
                "name": "get_context",
                "arguments": {}
            }
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Tool response:")
        print(f"  Content: {data.get('content', [{}])[0].get('text', 'N/A')}")
        if 'structuredContent' in data:
            context = data['structuredContent'].get('context', '')
            print(f"  Context length: {len(context)} chars")
            print(f"  Preview: {context[:100]}...")
    else:
        print(f"Error: {response.text}")
    
    # Test 4: Read a widget resource
    print("\n4. Testing read_resource (decision widget)...")
    response = requests.post(
        f"{BASE_URL}/mcp",
        headers=headers,
        cookies=cookies,
        json={
            "method": "read_resource",
            "params": {
                "uri": "ui://widget/decision"
            }
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Resource loaded:")
        print(f"  URI: {data.get('uri')}")
        print(f"  MIME Type: {data.get('mimeType')}")
        print(f"  HTML length: {len(data.get('text', ''))} chars")
    else:
        print(f"Error: {response.text}")
    
    print("\n" + "=" * 60)
    print("MCP Protocol Test Complete\n")


def main():
    print("DavidOS MCP Protocol Test")
    print("=" * 60)
    print("\nTo test authenticated endpoints, you need a session cookie.")
    print("\nSteps to get session cookie:")
    print("1. Open browser and go to:")
    print(f"   {BASE_URL}/login")
    print("2. Complete Google OAuth login")
    print("3. Open browser DevTools (F12)")
    print("4. Go to Application/Storage > Cookies")
    print(f"5. Find cookie named 'session' for {BASE_URL}")
    print("6. Copy the cookie value")
    print("\nThen run this script with the cookie:")
    print("  python test_mcp.py <session_cookie_value>")
    print("\n" + "=" * 60)
    
    if len(sys.argv) > 1:
        session_cookie = sys.argv[1]
        print(f"\nUsing provided session cookie: {session_cookie[:20]}...")
        test_with_session(session_cookie)
    else:
        print("\nNo session cookie provided. Testing without authentication...")
        print("(This will likely return 401 Unauthorized)\n")
        test_with_session()


if __name__ == "__main__":
    main()
