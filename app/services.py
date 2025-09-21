import socket
import time
import threading
import subprocess
import psutil
import signal
import os
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


class ServiceManager:
    """Manages starting and stopping services"""

    def __init__(self):
        self.managed_processes = {}  # Store process references

    def find_process_by_port(self, port: int) -> Optional[psutil.Process]:
        """Find process using a specific port"""
        try:
            for proc in psutil.process_iter(["pid", "name", "connections"]):
                try:
                    connections = proc.info["connections"]
                    if connections:
                        for conn in connections:
                            if conn.laddr.port == port:
                                return psutil.Process(proc.info["pid"])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error finding process on port {port}: {e}")
        return None

    def find_processes_by_name(self, name: str) -> List[psutil.Process]:
        """Find processes by name pattern"""
        processes = []
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    proc_info = proc.info
                    if name.lower() in proc_info["name"].lower() or any(
                        name.lower() in arg.lower()
                        for arg in (proc_info["cmdline"] or [])
                    ):
                        processes.append(psutil.Process(proc_info["pid"]))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error finding processes by name {name}: {e}")
        return processes

    def stop_service_by_port(self, port: int) -> Dict[str, Any]:
        """Stop service running on a specific port"""
        try:
            process = self.find_process_by_port(port)
            if not process:
                return {
                    "success": False,
                    "message": f"No process found running on port {port}",
                }

            process_info = {
                "pid": process.pid,
                "name": process.name(),
                "cmdline": " ".join(process.cmdline()),
            }

            # Try graceful shutdown first
            process.terminate()

            # Wait for process to terminate
            try:
                process.wait(timeout=5)
                return {
                    "success": True,
                    "message": f'Successfully stopped process {process_info["name"]} (PID: {process_info["pid"]}) on port {port}',
                    "process_info": process_info,
                }
            except psutil.TimeoutExpired:
                # Force kill if graceful shutdown failed
                process.kill()
                return {
                    "success": True,
                    "message": f'Force killed process {process_info["name"]} (PID: {process_info["pid"]}) on port {port}',
                    "process_info": process_info,
                }

        except psutil.NoSuchProcess:
            return {
                "success": False,
                "message": f"Process on port {port} no longer exists",
            }
        except psutil.AccessDenied:
            return {
                "success": False,
                "message": f"Access denied: Cannot stop process on port {port} (try running as administrator)",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error stopping service on port {port}: {str(e)}",
            }

    def stop_service_by_name(self, service_name: str) -> Dict[str, Any]:
        """Stop service by name/pattern"""
        try:
            processes = self.find_processes_by_name(service_name)
            if not processes:
                return {
                    "success": False,
                    "message": f'No processes found matching "{service_name}"',
                }

            stopped_processes = []
            errors = []

            for process in processes:
                try:
                    process_info = {
                        "pid": process.pid,
                        "name": process.name(),
                        "cmdline": " ".join(process.cmdline()),
                    }

                    process.terminate()
                    try:
                        process.wait(timeout=3)
                        stopped_processes.append(process_info)
                    except psutil.TimeoutExpired:
                        process.kill()
                        stopped_processes.append({**process_info, "force_killed": True})

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    errors.append(f"PID {process.pid}: {str(e)}")

            if stopped_processes:
                return {
                    "success": True,
                    "message": f'Stopped {len(stopped_processes)} process(es) matching "{service_name}"',
                    "stopped_processes": stopped_processes,
                    "errors": errors if errors else None,
                }
            else:
                return {
                    "success": False,
                    "message": f'Failed to stop any processes matching "{service_name}"',
                    "errors": errors,
                }

        except Exception as e:
            return {
                "success": False,
                "message": f'Error stopping service "{service_name}": {str(e)}',
            }

    def stop_docker_container(self, container_name: str) -> Dict[str, Any]:
        """Stop Docker container"""
        try:
            # Check if Docker is available
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": "Docker is not available on this system",
                }

            # Stop the container
            result = subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f'Successfully stopped Docker container "{container_name}"',
                }
            else:
                return {
                    "success": False,
                    "message": f'Failed to stop Docker container "{container_name}": {result.stderr}',
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": f'Timeout stopping Docker container "{container_name}"',
            }
        except FileNotFoundError:
            return {"success": False, "message": "Docker command not found"}
        except Exception as e:
            return {
                "success": False,
                "message": f'Error stopping Docker container "{container_name}": {str(e)}',
            }


class ServiceHistory:
    def __init__(self):
        self.history: Dict[str, List[ServiceResult]] = defaultdict(list)
        self.lock = threading.Lock()

    def add_result(self, result: ServiceResult):
        with self.lock:
            service_name = result.name
            self.history[service_name].append(result)

            # Clean old entries
            cutoff_time = datetime.now() - timedelta(hours=HISTORY_RETENTION_HOURS)
            self.history[service_name] = [
                r
                for r in self.history[service_name]
                if r.timestamp and datetime.fromtimestamp(r.timestamp) > cutoff_time
            ]

    def get_history(self, service_name: str, limit: int = 50) -> List[ServiceResult]:
        with self.lock:
            return self.history.get(service_name, [])[-limit:]

    def get_uptime_percentage(self, service_name: str, hours: int = 24) -> float:
        with self.lock:
            recent_results = self.get_history(service_name, 100)
            if not recent_results:
                return 0.0

            successful_checks = len(
                [r for r in recent_results if r.status in ["up", "open"]]
            )

            return (successful_checks / len(recent_results)) * 100


class EnhancedServiceChecker:
    """Enhanced service checker with detailed descriptions and monitoring"""

    def __init__(self):
        self.history = ServiceHistory()
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.manager = ServiceManager()

    def get_port_description(self, port: int) -> str:
        """Get detailed description for a port including common services"""
        common_ports = {
            21: "FTP - File Transfer Protocol",
            22: "SSH - Secure Shell",
            23: "Telnet",
            25: "SMTP - Simple Mail Transfer Protocol",
            53: "DNS - Domain Name System",
            80: "HTTP - HyperText Transfer Protocol",
            110: "POP3 - Post Office Protocol v3",
            143: "IMAP - Internet Message Access Protocol",
            443: "HTTPS - HTTP Secure",
            993: "IMAPS - IMAP over SSL",
            995: "POP3S - POP3 over SSL",
            3000: "Node.js Development Server",
            3001: "React Development Server (Alt)",
            4200: "Angular Development Server",
            5000: "Flask Development Server",
            5432: "PostgreSQL Database",
            6379: "Redis Database",
            8000: "Django Development Server / HTTP Alt",
            8080: "HTTP Alternative / Tomcat",
            9000: "PHP-FPM / SonarQube",
            27017: "MongoDB Database",
            3306: "MySQL/MariaDB Database",
        }

        if port in common_ports:
            return f"Port {port} - {common_ports[port]}"
        elif 3000 <= port <= 3999:
            return f"Port {port} - Likely Development Server"
        elif 8000 <= port <= 8999:
            return f"Port {port} - Likely Web Server/API"
        else:
            return f"Port {port} - Custom Service"

    def check_port_service(
        self, host: str, port: int, timeout: float = DEFAULT_TIMEOUT
    ) -> ServiceResult:
        start_time = time.time()
        description = self.get_port_description(port)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            response_time = (time.time() - start_time) * 1000

            if result == 0:
                status = "open"
                details = f"{description} is accessible"
                error_message = None
            else:
                status = "closed"
                details = f"{description} is not accessible"
                error_message = f"Connection refused to {host}:{port}"

        except socket.timeout:
            response_time = timeout * 1000
            status = "timeout"
            details = f"{description} - Connection timeout"
            error_message = f"Timeout connecting to {host}:{port} after {timeout}s"
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            status = "error"
            details = f"{description} - Connection error"
            error_message = str(e)

        result = ServiceResult(
            name=f"Port {port} Service Check",
            status=status,
            response_time=response_time,
            error_message=error_message,
            details=details,
            timestamp=time.time(),
        )

        self.history.add_result(result)
        return result

    def check_http_service(
        self,
        url: str,
        timeout: float = DEFAULT_TIMEOUT,
        expected_status: Optional[int] = None,
        method: str = "GET",
    ) -> ServiceResult:
        start_time = time.time()
        parsed = urlparse(url)

        try:
            response = requests.request(method, url, timeout=timeout)
            response_time = (time.time() - start_time) * 1000

            expected = expected_status or 200

            if response.status_code == expected:
                status = "up"
                error_message = None
                details = self._get_http_description(parsed, response)
            else:
                status = "down"
                error_message = (
                    f"Expected status {expected}, got {response.status_code}"
                )
                details = (
                    f"HTTP service returned unexpected status: {response.status_code}"
                )

        except requests.exceptions.Timeout:
            response_time = timeout * 1000
            status = "timeout"
            error_message = f"Request timeout after {timeout}s"
            details = f"HTTP service at {parsed.netloc} timed out"
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            status = "down"
            error_message = "Connection refused"
            details = f"Cannot connect to HTTP service at {parsed.netloc}"
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            status = "error"
            error_message = str(e)
            details = f"Error checking HTTP service at {parsed.netloc}"

        result = ServiceResult(
            name=f"HTTP Service: {url}",
            status=status,
            response_time=response_time,
            error_message=error_message,
            details=details,
            timestamp=time.time(),
        )

        self.history.add_result(result)
        return result

    def _get_http_description(self, parsed: urlparse, response) -> str:
        try:
            server = response.headers.get("Server", "Unknown")
            content_type = response.headers.get("Content-Type", "Unknown")
            return f"HTTP service at {parsed.netloc} is responding (Server: {server}, Content-Type: {content_type})"
        except:
            return f"HTTP service at {parsed.netloc} is responding"

    def check_multiple_services(self, services: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []

        for service in services:
            if service.get("type") == "http":
                result = self.check_http_service(service["url"])
            elif service.get("type") == "port":
                result = self.check_port_service(
                    service.get("host", "localhost"), service["port"]
                )
            else:
                continue

            results.append(result.to_dict())

        return {
            "total_services": len(results),
            "online_services": len(
                [r for r in results if r["status"] in ["up", "open"]]
            ),
            "services": results,
            "timestamp": time.time(),
        }
