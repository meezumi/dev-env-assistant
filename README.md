# Local-Host Dev-Env Assistant for Claude

An AI-powered tool to check the health and status of your local development environment directly from your AI assistant.

---

## Overview

As developers, we constantly need to check if our local services are running before we start working. Is the database up? Is the backend API responding? Is the React dev server running?

This project is a **Model Context Protocol (MCP) server** that grants an AI assistant, like Claude, the ability to perform these checks for you. By connecting this tool, you can ask Claude in natural language to verify your setup, saving you time and streamlining your workflow.

---

## Features

- **Check Specific Ports:** Instantly verify if any port is open on your local machine (e.g., for databases like PostgreSQL, MongoDB, Redis).
- **Check HTTP Services:** Check if a web server, API endpoint, or other HTTP service is running and see its status code.
- **Environment Presets:** Use convenient presets to check a whole group of common services at once, such as `web_dev`, `backend`, `databases`, or `tools`.
- **Custom Service Checks:** Define your own list of services to check on the fly.
- **Discoverable:** Ask the tool what presets are available to see what it can do.

---

## Prerequisites

- Python 3.8+
- The Claude Desktop App

---

## Installation

Follow these steps to set up the tool on your local machine.

### 1. Create the `requirements.txt` File

In your `dev-env-assistant` folder, create a new file named `requirements.txt` and add the following lines:

```txt
mcp>=0.1.0
requests>=2.31.0
```

### 2. Clone or Download the Project

Get a copy of this project on your machine.

### 3. Navigate to the Project Directory

Open your terminal and `cd` into the project folder:

```bash
cd path/to/dev-env-assistant
```

### 4. Create and Activate a Virtual Environment

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

### 5. Install Required Packages

Install all necessary Python libraries from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

---

## Configuration & Usage

This tool connects to the Claude Desktop App using the STDIO (Standard I/O) method. The app will run the Python script for you in the background.

To configure this connection, follow the specific steps within the Claude app's settings.

For a detailed, step-by-step guide with screenshots on how to add this tool to the Claude Desktop App, please refer to the official documentation or the specific instructions provided at the URL where you obtained this script.

**Refer to this URL for the complete, step-by-step guide:**  
[\[Link to the conversation\]](https://modelcontextprotocol.io/quickstart/user)

Once configured, simply open a new chat in the Claude app, ensure the "Dev Environment Assistant" tool is enabled, and start making requests!

---

## Example Prompts

Here are a few things you can ask once the tool is active:

- "What service presets are available?"
- "Check my database environment for me."
- "Is my Postgres database running on port 5432?"
- "Can you check if my web server at http://localhost:3000 is up?"
- "Run a check on the 'backend' preset and also check for a custom service on port 8888."

---

