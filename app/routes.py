from flask import jsonify, render_template, request
from app import app, checker, config


@app.route("/")
def dashboard():
    """Main dashboard page"""
    return render_template("dashboard.html", title="Dev Environment Assistant")


@app.route("/api/check/<service_type>", methods=["POST"])
def check_service(service_type):
    """API endpoint for service checks"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        if service_type == "port":
            port = data.get("port")
            host = data.get("host", "localhost")

            if not port:
                return jsonify({"error": "Port is required"}), 400

            try:
                port = int(port)
            except (TypeError, ValueError):
                return jsonify({"error": "Port must be a number"}), 400

            result = checker.check_port_service(host, port)
            return jsonify(result.to_dict())

        elif service_type == "http":
            url = data.get("url")
            if not url:
                return jsonify({"error": "URL is required"}), 400

            result = checker.check_http_service(url)
            return jsonify(result.to_dict())

        elif service_type == "batch":
            services = data.get("services", [])
            if not services:
                return jsonify({"error": "Services list is required"}), 400

            result = checker.check_multiple_services(services)
            return jsonify(result)

        else:
            return jsonify({"error": f"Invalid service type: {service_type}"}), 400

    except Exception as e:
        print(f"Error in check_service: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/api/services/<category>")
def get_category_services(category):
    """Get services for a specific category"""
    try:
        if category == "all":
            services = config.get_services()
        else:
            services = config.get_services(category)
        return jsonify(services)
    except Exception as e:
        print(f"Error in get_category_services: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/history/<service_name>")
def get_service_history(service_name):
    """Get historical data for a service"""
    try:
        limit = int(request.args.get("limit", 50))
        history = checker.history.get_history(service_name, limit)
        uptime = checker.history.get_uptime_percentage(service_name)
        return jsonify(
            {
                "service": service_name,
                "history": [r.to_dict() for r in history],
                "uptime_percentage": uptime,
            }
        )
    except Exception as e:
        print(f"Error in get_service_history: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/config", methods=["GET", "PUT"])
def handle_config():
    """Handle configuration operations"""
    try:
        if request.method == "GET":
            return jsonify(config.config)
        elif request.method == "PUT":
            new_config = request.get_json()
            if not new_config:
                return jsonify({"error": "No configuration data provided"}), 400

            config.config.update(new_config)
            config.save_config()
            return jsonify({"message": "Configuration updated successfully"})
    except Exception as e:
        print(f"Error in handle_config: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/monitoring/status")
def monitoring_status():
    """Monitoring status page"""
    try:
        all_services = config.get_services()
        service_stats = {}
        total_services = 0

        for category, services in all_services.items():
            if services:
                total_services += len(services)
                for service in services:
                    service_name = f"{service['name']} ({service['type']})"
                    uptime = checker.history.get_uptime_percentage(service_name)
                    recent_history = checker.history.get_history(service_name, 10)

                    service_stats[service_name] = {
                        "uptime": uptime,
                        "recent_checks": len(recent_history),
                        "last_status": (
                            recent_history[-1].status if recent_history else "unknown"
                        ),
                    }

        return jsonify(
            {
                "total_services": total_services,
                "service_stats": service_stats,
                "monitoring_enabled": config.config.get("monitoring", {}).get(
                    "enabled", False
                ),
            }
        )
    except Exception as e:
        print(f"Error in monitoring_status: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500
