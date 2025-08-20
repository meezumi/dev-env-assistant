"""
Dev Environment Assistant MCP Server

This MCP server provides tools to check the status of local development services.
It can check if ports are open, test HTTP endpoints, and verify database connections.
"""

import asyncio
import json
import socket
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from mcp.server.models import InitializationOptions, ServerCapabilities
from mcp.server import Server
from mcp.types import (
    CallToolRequest,
    CallToolRequestParams,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
    INTERNAL_ERROR,
    INVALID_PARAMS,
)

# Create the server instance
server = Server("dev-environment-assistant")


class ServiceChecker:
    """Utility class for checking various types of services"""

    @staticmethod
    def check_port(
        host: str = "localhost", port: int = 8080, timeout: float = 3.0
    ) -> Dict[str, Any]:
        """Check if a port is open on the given host"""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return {
                    "status": "open",
                    "host": host,
                    "port": port,
                    "message": f"Port {port} is open on {host}",
                }
        except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError) as e:
            return {
                "status": "closed",
                "host": host,
                "port": port,
                "message": f"Port {port} is closed on {host}: {str(e)}",
            }

    @staticmethod
    def check_http_service(
        url: str, timeout: float = 5.0, expected_status: Optional[int] = None
    ) -> Dict[str, Any]:
        """Check if an HTTP service is responding"""
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True)

            status_ok = True
            if expected_status and response.status_code != expected_status:
                status_ok = False

            return {
                "status": "up" if status_ok else "unhealthy",
                "url": url,
                "status_code": response.status_code,
                "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                "message": f"HTTP service responded with {response.status_code}",
            }
        except requests.exceptions.Timeout:
            return {
                "status": "timeout",
                "url": url,
                "message": f"HTTP service timed out after {timeout}s",
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "down",
                "url": url,
                "message": "Connection refused - service appears to be down",
            }
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "message": f"Error checking HTTP service: {str(e)}",
            }

    @staticmethod
    def check_multiple_services(services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check multiple services and return a summary"""
        results = []
        all_healthy = True

        for service in services:
            service_type = service.get("type", "port")

            if service_type == "port":
                result = ServiceChecker.check_port(
                    host=service.get("host", "localhost"),
                    port=service["port"],
                    timeout=service.get("timeout", 3.0),
                )
                result["name"] = service.get("name", f"Port {service['port']}")

            elif service_type == "http":
                result = ServiceChecker.check_http_service(
                    url=service["url"],
                    timeout=service.get("timeout", 5.0),
                    expected_status=service.get("expected_status"),
                )
                result["name"] = service.get("name", service["url"])

            else:
                result = {
                    "status": "error",
                    "name": service.get("name", "Unknown"),
                    "message": f"Unknown service type: {service_type}",
                }

            results.append(result)

            if result["status"] not in ["open", "up"]:
                all_healthy = False

        return {
            "overall_status": "healthy" if all_healthy else "unhealthy",
            "services": results,
            "summary": f"{len([r for r in results if r['status'] in ['open', 'up']])}/{len(results)} services are healthy",
        }


# Common development service configurations
COMMON_SERVICES = {
    "web_dev": [
        {"name": "React Dev Server", "type": "http", "url": "http://localhost:3000"},
        {"name": "Vue Dev Server", "type": "http", "url": "http://localhost:8080"},
        {"name": "Angular Dev Server", "type": "http", "url": "http://localhost:4200"},
        {"name": "Next.js Dev Server", "type": "http", "url": "http://localhost:3000"},
    ],
    "backend": [
        {"name": "Express Server", "type": "http", "url": "http://localhost:3000"},
        {"name": "Django Dev Server", "type": "http", "url": "http://localhost:8000"},
        {"name": "Flask Dev Server", "type": "http", "url": "http://localhost:5000"},
        {"name": "FastAPI Server", "type": "http", "url": "http://localhost:8000"},
        {"name": "Rails Server", "type": "http", "url": "http://localhost:3000"},
    ],
    "databases": [
        {"name": "PostgreSQL", "type": "port", "port": 5432},
        {"name": "MySQL", "type": "port", "port": 3306},
        {"name": "MongoDB", "type": "port", "port": 27017},
        {"name": "Redis", "type": "port", "port": 6379},
    ],
    "tools": [
        {"name": "Docker", "type": "http", "url": "http://localhost:2375"},
        {"name": "Elasticsearch", "type": "http", "url": "http://localhost:9200"},
        {
            "name": "RabbitMQ Management",
            "type": "http",
            "url": "http://localhost:15672",
        },
        {"name": "Mailhog", "type": "http", "url": "http://localhost:8025"},
    ],
}


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools for checking development services"""
    return ListToolsResult(
        tools=[
            Tool(
                name="check_port",
                description="Check if a specific port is open on localhost or another host",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "port": {
                            "type": "integer",
                            "description": "Port number to check",
                            "minimum": 1,
                            "maximum": 65535,
                        },
                        "host": {
                            "type": "string",
                            "description": "Host to check (default: localhost)",
                            "default": "localhost",
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in seconds (default: 3.0)",
                            "default": 3.0,
                            "minimum": 0.1,
                            "maximum": 30.0,
                        },
                    },
                    "required": ["port"],
                },
            ),
            Tool(
                name="check_http_service",
                description="Check if an HTTP service is responding at a given URL",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to check (e.g., http://localhost:3000)",
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in seconds (default: 5.0)",
                            "default": 5.0,
                            "minimum": 0.1,
                            "maximum": 30.0,
                        },
                        "expected_status": {
                            "type": "integer",
                            "description": "Expected HTTP status code (optional)",
                            "minimum": 100,
                            "maximum": 599,
                        },
                    },
                    "required": ["url"],
                },
            ),
            Tool(
                name="check_dev_environment",
                description="Check multiple common development services at once",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "preset": {
                            "type": "string",
                            "description": "Preset configuration to check",
                            "enum": ["web_dev", "backend", "databases", "tools", "all"],
                        },
                        "custom_services": {
                            "type": "array",
                            "description": "Custom services to check",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {
                                        "type": "string",
                                        "enum": ["port", "http"],
                                    },
                                    "port": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 65535,
                                    },
                                    "host": {"type": "string", "default": "localhost"},
                                    "url": {"type": "string"},
                                    "timeout": {
                                        "type": "number",
                                        "minimum": 0.1,
                                        "maximum": 30.0,
                                    },
                                    "expected_status": {
                                        "type": "integer",
                                        "minimum": 100,
                                        "maximum": 599,
                                    },
                                },
                            },
                        },
                    },
                },
            ),
            Tool(
                name="get_service_presets",
                description="Get information about available service presets",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]
    )


@server.call_tool()
async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls for checking development services"""

    try:
        if request.name == "check_port":
            args = request.arguments or {}
            port = args.get("port")
            host = args.get("host", "localhost")
            timeout = args.get("timeout", 3.0)

            if not isinstance(port, int) or port < 1 or port > 65535:
                raise ValueError("Port must be an integer between 1 and 65535")

            result = ServiceChecker.check_port(host=host, port=port, timeout=timeout)

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2))]
            )

        elif request.name == "check_http_service":
            args = request.arguments or {}
            url = args.get("url")
            timeout = args.get("timeout", 5.0)
            expected_status = args.get("expected_status")

            if not url:
                raise ValueError("URL is required")

            # Basic URL validation
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")

            result = ServiceChecker.check_http_service(
                url=url, timeout=timeout, expected_status=expected_status
            )

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2))]
            )

        elif request.name == "check_dev_environment":
            args = request.arguments or {}
            preset = args.get("preset")
            custom_services = args.get("custom_services", [])

            services = []

            # Add preset services
            if preset == "all":
                for category in COMMON_SERVICES.values():
                    services.extend(category)
            elif preset in COMMON_SERVICES:
                services.extend(COMMON_SERVICES[preset])

            # Add custom services
            services.extend(custom_services)

            if not services:
                return CallToolResult(
                    content=[
                        TextContent(type="text", text="No services specified to check")
                    ]
                )

            result = ServiceChecker.check_multiple_services(services)

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2))]
            )

        elif request.name == "get_service_presets":
            preset_info = {
                "available_presets": list(COMMON_SERVICES.keys()) + ["all"],
                "preset_details": {
                    category: [
                        {
                            "name": service.get("name", "Unknown"),
                            "type": service.get("type", "unknown"),
                            "details": service.get("url")
                            or f"Port {service.get('port', 'unknown')}",
                        }
                        for service in services
                    ]
                    for category, services in COMMON_SERVICES.items()
                },
            }

            return CallToolResult(
                content=[
                    TextContent(type="text", text=json.dumps(preset_info, indent=2))
                ]
            )

        else:
            raise ValueError(f"Unknown tool: {request.name}")

    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")], isError=True
        )


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="dev-environment-assistant",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None, experimental_capabilities={}
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
