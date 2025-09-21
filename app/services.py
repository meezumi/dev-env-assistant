import socket
import time
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

import requests
from app.models import ServiceResult

# Constants
DEFAULT_TIMEOUT = 5.0
MAX_WORKERS = 10
HISTORY_RETENTION_HOURS = 24

class ServiceHistory:
    def __init__(self):
        self.history: Dict[str, List[ServiceResult]] = defaultdict(list)
        self.lock = threading.Lock()

    def add_result(self, result: ServiceResult):
        with self.lock:
            self.history[result.name].append(result)
            # Keep only recent history
            cutoff = datetime.now() - timedelta(hours=HISTORY_RETENTION_HOURS)
            self.history[result.name] = [
                r for r in self.history[result.name]
                if r.last_checked > cutoff
            ]

    def get_history(self, service_name: str, limit: int = 50) -> List[ServiceResult]:
        with self.lock:
            return self.history[service_name][-limit:]

    def get_uptime_percentage(self, service_name: str, hours: int = 24) -> float:
        with self.lock:
            recent_results = [
                r for r in self.history[service_name][-100:]  # Last 100 checks
                if r.last_checked > datetime.now() - timedelta(hours=hours)
            ]
            if not recent_results:
                return 0.0

            successful = sum(1 for r in recent_results if r.status in ["open", "up", "online"])
            return (successful / len(recent_results)) * 100


class EnhancedServiceChecker:
    """Enhanced service checker with detailed descriptions and monitoring"""

    def __init__(self):
        self.history = ServiceHistory()
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    def get_port_description(self, port: int) -> str:
        """Get detailed description for a port including common services"""
        port_info = {
            22: "SSH (Secure Shell) - Remote secure access to system",
            25: "SMTP (Simple Mail Transfer Protocol) - Email sending",
            53: "DNS (Domain Name System) - Domain name resolution",
            80: "HTTP (Hypertext Transfer Protocol) - Web server",
            110: "POP3 (Post Office Protocol) - Email retrieval",
            143: "IMAP (Internet Message Access Protocol) - Email access",
            443: "HTTPS (HTTP Secure) - Secure web server",
            587: "SMTP (Submission) - Authenticated email sending",
            993: "IMAPS - Secure IMAP (email retrieval over SSL/TLS)",
            995: "POP3S - Secure POP3 (email retrieval over SSL/TLS)",
            3306: "MySQL Database Server - Relational database service",
            5432: "PostgreSQL Database Server - Advanced SQL database",
            27017: "MongoDB Database Server - NoSQL document database",
            6379: "Redis Cache Server - In-memory data structure store",
            9200: "Elasticsearch Search Engine - Full-text search and analytics",
            15672: "RabbitMQ Management - Message broker admin interface",
            8080: "HTTP Alternate - Common for development web servers",
            3000: "React/Express Development Server - Node.js applications",
            4000: "Next.js Development Server - React framework",
            4200: "Angular Development Server - Google framework",
            5000: "Flask Development Server - Python web framework",
            8000: "Django/FastAPI Development Server - Python frameworks",
            8025: "MailHog Web UI - Email testing tool for development",
            8081: "Alternative HTTP - Secondary web server port",
            9000: "PHP Development Server - Primary PHP development port",
            9080: "WebSphere Application Server - Java EE server (default)",
        }

        base_info = port_info.get(port, f"Port {port} - Custom/Application Specific Service")
        applications = [
            "Development servers", "Database systems", "Message brokers",
            "Search engines", "Mail servers", "Cache systems", "Web services"
        ]
        return f"{base_info} | Category: {' | '.join(applications)}"

    def check_port_service(self, host: str, port: int, timeout: float = DEFAULT_TIMEOUT) -> ServiceResult:
        """Check if a port is open with detailed information"""
        result = ServiceResult(
            name=f"Port {port} Service Check",
            type="port",
            host=host,
            port=port,
            status="checking"
        )

        try:
            start_time = time.time()
            sock = socket.create_connection((host, port), timeout)
            response_time = (time.time() - start_time) * 1000

            # Try to get service information
            try:
                peer_info = sock.getpeername()
                local_info = sock.getsockname()
                sock.close()

                result.status = "open"
                result.response_time = round(response_time, 2)
                result.additional_info = {
                    "description": self.get_port_description(port),
                    "peer_address": f"{peer_info[0]}:{peer_info[1]}",
                    "local_address": f"{local_info[0]}:{local_info[1]}",
                    "connection_established": True
                }
                result.error_message = None
            except Exception:
                sock.close()
                raise

        except socket.timeout:
            result.status = "timeout"
            result.error_message = f"Connection timeout after {timeout}s"
            result.additional_info = {
                "description": self.get_port_description(port),
                "timeout_reason": "No response within configured timeout"
            }
        except socket.gaierror as e:
            result.status = "error"
            result.error_message = f"DNS resolution failed: {str(e)}"
            result.additional_info = {
                "description": self.get_port_description(port),
                "dns_error": True
            }
        except ConnectionRefusedError:
            result.status = "closed"
            result.error_message = "Connection refused - service not running or blocking connections"
            result.additional_info = {
                "description": self.get_port_description(port),
                "connection_refused": True
            }
        except Exception as e:
            result.status = "error"
            result.error_message = f"Network error: {str(e)}"
            result.additional_info = {
                "description": self.get_port_description(port),
                "unknown_error": True
            }

        self.history.add_result(result)
        return result

    def check_http_service(self, url: str, timeout: float = DEFAULT_TIMEOUT,
                          expected_status: Optional[int] = None,
                          method: str = "GET") -> ServiceResult:
        """Check HTTP service with comprehensive diagnostics"""
        parsed = urlparse(url)
        result = ServiceResult(
            name=f"HTTP Service: {url}",
            type="http",
            url=url,
            status="checking"
        )

        try:
            start_time = time.time()
            response = requests.request(
                method=method,
                url=url,
                timeout=timeout,
                allow_redirects=True,
                headers={"User-Agent": "DevEnvironmentAssitant/1.0"}
            )
            response_time = (time.time() - start_time) * 1000

            status_ok = True
            if expected_status and response.status_code != expected_status:
                status_ok = False

            result.status = "up" if status_ok else "unhealthy"
            result.response_time = round(response_time, 2)
            result.status_code = response.status_code

            result.additional_info = {
                "description": self._get_http_description(parsed, response),
                "headers_count": len(response.headers),
                "content_length": len(response.text),
                "encoding": response.encoding,
                "redirect_history": len(response.history),
                "final_url": response.url,
                "is_https": parsed.scheme == "https",
                "domain": parsed.netloc
            }
            result.error_message = None

            # HTTP headers analysis
            security_headers = {
                "X-Content-Type-Options": response.headers.get("X-Content-Type-Options"),
                "Content-Security-Policy": response.headers.get("Content-Security-Policy") is not None,
                "X-Frame-Options": response.headers.get("X-Frame-Options"),
                "Strict-Transport-Security": response.headers.get("Strict-Transport-Security") is not None
            }
            result.additional_info["security_headers"] = security_headers

        except requests.exceptions.Timeout:
            result.status = "timeout"
            result.error_message = f"HTTP request timed out after {timeout}s"
            result.additional_info = {
                "description": f"HTTP service at {url} - timeout occurred",
                "timeout_value": timeout
            }
        except requests.exceptions.ConnectionError:
            result.status = "down"
            result.error_message = "Connection failed - service unreachable"
            result.additional_info = {
                "description": f"HTTP service at {url} - connection failed",
                "connection_error": True
            }
        except requests.exceptions.HTTPError as e:
            result.status = "error"
            result.status_code = e.response.status_code if hasattr(e, 'response') else None
            result.error_message = f"HTTP error: {str(e)}"
            result.additional_info = {
                "description": f"HTTP service at {url} - HTTP error occurred"
            }
        except Exception as e:
            result.status = "error"
            result.error_message = f"HTTP service error: {str(e)}"
            result.additional_info = {
                "description": f"HTTP service at {url} - general error occurred"
            }

        self.history.add_result(result)
        return result

    def _get_http_description(self, parsed: urlparse, response) -> str:
        """Generate descriptive information for HTTP services"""
        port_info = ""
        if parsed.port:
            port_info = f":{parsed.port}"

        descriptions = {
            3000: "React Development Server - Frontend JavaScript framework development",
            4000: "Next.js Development Server - Full-stack React framework",
            4200: "Angular Development Server - Enterprise TypeScript framework",
            5000: "Flask Development Server - Python micro web framework",
            8000: "Django/FastAPI Development Server - Python web frameworks",
            8080: "Alternative Web Server - Development and production alternatives",
            9200: "Elasticsearch REST API - Search and analytics engine",
            15672: "RabbitMQ Management Interface - Message broker management",
            2375: "Docker Engine API - Container runtime management",
            8025: "MailHog Web Interface - Email testing tool"
        }

        base_desc = descriptions.get(parsed.port or 80,
                                   f"HTTP Service on {parsed.hostname}{port_info}")

        if response:
            content_type = response.headers.get('content-type', '').lower()
            if 'json' in content_type:
                base_desc += " | API Endpoint (JSON)"
            elif 'html' in content_type:
                base_desc += " | Web Application"
            elif 'xml' in content_type:
                base_desc += " | XML API Service"
            else:
                base_desc += " | Generic HTTP Service"

        return base_desc

    def check_multiple_services(self, services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check multiple services concurrently with detailed reporting"""
        results = []
        futures = []

        # Submit all checks concurrently
        for service in services:
            if service.get("type") == "port":
                future = self.executor.submit(
                    self.check_port_service,
                    service.get("host", "localhost"),
                    service["port"],
                    service.get("timeout", DEFAULT_TIMEOUT)
                )
                futures.append((future, service))
            elif service.get("type") == "http":
                future = self.executor.submit(
                    self.check_http_service,
                    service["url"],
                    service.get("timeout", DEFAULT_TIMEOUT),
                    service.get("expected_status"),
                    service.get("method", "GET")
                )
                futures.append((future, service))

        # Collect results
        all_healthy = True
        for future, service in futures:
            try:
                result = future.result(timeout=30)
                results.append(asdict(result))

                if result.status not in ["open", "up", "online"]:
                    all_healthy = False
            except Exception as e:
                error_result = ServiceResult(
                    name=service.get("name", f"Error checking {service.get('type', 'unknown')}"),
                    type=service.get("type", "unknown"),
                    status="error",
                    error_message=str(e),
                    additional_info={"executor_error": True}
                )
                results.append(asdict(error_result))
                all_healthy = False

        # Generate statistics
        status_counts = defaultdict(int)
        response_times = []

        for result in results:
            status_counts[result["status"]] += 1
            if result.get("response_time"):
                response_times.append(result["response_time"])

        avg_response_time = sum(response_times) / len(response_times) if response_times else None

        return {
            "overall_status": "healthy" if all_healthy else "unhealthy",
            "services": results,
            "statistics": {
                "total_services": len(results),
                "healthy_count": sum(1 for r in results if r["status"] in ["open", "up", "online"]),
                "unhealthy_count": sum(1 for r in results if r["status"] not in ["open", "up", "online"]),
                "status_distribution": dict(status_counts),
                "average_response_time_ms": round(avg_response_time, 2) if avg_response_time else None
            },
            "summary": f"{len([r for r in results if r['status'] in ['open', 'up', 'online']])}/{len(results)} services healthy",
            "timestamp": datetime.now().isoformat()
        }
