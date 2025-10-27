# Local-firewall

Lightweight local firewall management tool with a Python backend and an HTML-based UI for configuring firewall rules on a single machine.

## Table of Contents
- Features
- Requirements
- Installation
- Configuration
- Usage
- Development
- Contributing
- License
- Contact

## Features
- Add, remove, and list local firewall rules
- Block or allow IP addresses and ranges
- Manage port-based rules
- Simple HTML UI for local administration
- Persist rules across restarts (if configured)

## Requirements
- Linux (tested on Ubuntu/CentOS) — or other OS with iptables/nftables support
- Python 3.8+
- pip

## Installation
1. Clone the repo:
   git clone https://github.com/vivekrautela56/Local-firewall.git
2. Enter the project directory:
   cd Local-firewall
3. (Optional) Create a virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate
4. Install dependencies (if requirements.txt exists):
   pip install -r requirements.txt
   If there is no requirements.txt, install Flask or other dependencies as needed, for example:
   pip install flask

## Configuration
- Review and update configuration files (if any) under the repo root or a config/ directory.
- Ensure the service runs with necessary privileges to modify firewall rules (may require sudo/root).

## Usage
- Start the backend (example):
  python app.py
  or
  flask run --host=0.0.0.0 --port=5000
- Open the UI in your browser:
  http://localhost:5000
- CLI usage examples (replace with actual script names if present):
  - Add rule: python manage_rules.py add --ip 1.2.3.4 --action block
  - List rules: python manage_rules.py list

Replace commands above with the actual entrypoints in this repository. If you provide the main script name (for example app.py, server.py, or run.py), this README will be updated with exact usage examples.

## Development
- Run tests (if any):
  pytest
- Coding style: follow PEP8. Use black/isort if desired.

## Contributing
- Fork the repo
- Create a feature branch: git checkout -b feature-name
- Commit your changes and open a pull request
- Please include tests for new features and ensure existing tests pass

## License
This project does not include a LICENSE file yet. If you want an MIT license, let me know and I can add one.

## Contact
Maintainer: @vivekrautela56
