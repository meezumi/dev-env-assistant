
from dataclasses import asdict
from flask import jsonify, render_template, request
from app import app, checker, config

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html',
                         title="Dev Environment Assistant")

@app.route('/api/check/<service_type>', methods=['POST'])
def check_service(service_type):
    """API endpoint for service checks"""
    data = request.get_json()

    try:
        if service_type == "port":
            port = data.get("port")
            host = data.get("host", "localhost")
            if not port:
                return jsonify({"error": "Port is required"}), 400

            result = checker.check_port_service(host, port)
            return jsonify(asdict(result))

        elif service_type == "http":
            url = data.get("url")
            if not url:
                return jsonify({"error": "URL is required"}), 400

            result = checker.check_http_service(
                url,
                expected_status=data.get("expected_status"),
                method=data.get("method", "GET")
            )
            return jsonify(asdict(result))

        elif service_type == "batch":
            services = data.get("services", [])
            if not services:
                return jsonify({"error": "Services list is required"}), 400

            result = checker.check_multiple_services(services)
            return jsonify(result)

        else:
            return jsonify({"error": "Invalid service type"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/services/<category>')
def get_category_services(category):
    """Get services for a specific category"""
    if category == "all":
        services = config.get_services()
    else:
        services = {category: config.get_services(category)}
    return jsonify(services)

@app.route('/api/history/<service_name>')
def get_service_history(service_name):
    """Get historical data for a service"""
    limit = int(request.args.get('limit', 50))
    history = checker.history.get_history(service_name, limit)
    uptime = checker.history.get_uptime_percentage(service_name)
    return jsonify({
        "service": service_name,
        "history": [asdict(r) for r in history],
        "uptime_percentage": uptime
    })

@app.route('/api/config', methods=['GET', 'PUT'])
def handle_config():
    """Handle configuration operations"""
    if request.method == 'GET':
        return jsonify(config.config)
    elif request.method == 'PUT':
        try:
            new_config = request.get_json()
            config.config.update(new_config)
            config.save_config()
            return jsonify({"message": "Configuration updated"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
