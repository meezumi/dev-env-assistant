# Dev Env Assistant

A simple web application to monitor the health and status of your local development environment.

![alt text](<Screenshot 2025-09-21 211214.png>)

---

## Overview

This tool provides a web dashboard to check if your local services like databases, backend APIs, and frontend development servers are running.

---

## Features

- **Check Specific Ports:** Instantly verify if any port is open on your local machine.
- **Check HTTP Services:** Check if a web server, API endpoint, or other HTTP service is running and see its status code.
- **Environment Presets:** Use convenient presets to check a whole group of common services at once, such as `web_dev`, `backend`, `databases`, or `tools`.
- **Custom Service Checks:** Define your own list of services to check in the `dev_assistant_config.json` file.

---

## Prerequisites

- Python 3.8+

---

## Installation

Follow these steps to set up the tool on your local machine.

### 1. Clone or Download the Project

Get a copy of this project on your machine.

### 2. Navigate to the Project Directory

Open your terminal and `cd` into the project folder:

```bash
cd path/to/dev-env-assistant
```

### 3. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment to keep dependencies isolated.

```bash
# Create the environment
python -m venv venv

# Activate the environment
# On Windows:
.\venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate
```

### 4. Install Required Packages

Install all necessary Python libraries from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

---

## Usage

To start the application, run the `run.py` script:

```bash
python run.py
```

This will start a web server on `http://localhost:5000`. Open this URL in your browser to see the dashboard.

---

## Configuration

You can configure the services to monitor by editing the `dev_assistant_config.json` file. This file is created automatically when you first run the application.

You can add your own services to the `services` section of the JSON file. For example:

```json
{
  "services": {
    "my_services": [
      {
        "name": "My App",
        "type": "http",
        "url": "http://localhost:8080"
      },
      {
        "name": "My Database",
        "type": "port",
        "port": 1234
      }
    ]
  }
}
```
![alt text](<Screenshot 2025-09-21 212218.png>)