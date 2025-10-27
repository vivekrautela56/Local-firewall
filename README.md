# Local-firewall

Lightweight local firewall management tool with a Python backend and an HTML-based UI for configuring firewall rules on a single machine.

## Table of Contents
- Features
- Requirements
- Installation
- Configuration
- Usage (Running)
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
- Linux (recommended) with iptables or nftables installed
- Python 3.8+
- pip
- Root or sudo privileges to modify system firewall rules (iptables/nftables)

## Installation
Follow these steps to install and run the project on your machine.

1) Clone the repository
   git clone https://github.com/vivekrautela56/Local-firewall.git
   cd Local-firewall

2) Create and activate a Python virtual environment (recommended)
   python3 -m venv .venv
   source .venv/bin/activate

3) Install Python dependencies
   - If the repository contains requirements.txt:
     pip install -r requirements.txt
   - If no requirements.txt is present, install common dependencies used by web backends:
     pip install flask
     (Also install any other dependency used by the project.)

4) Optional: Configure a system user and permissions
   - The service needs permission to modify firewall rules. You can either run the service as root (not recommended for long-running web servers) or grant limited sudo privileges to the service user for the specific firewall helper scripts.
   - Example sudoers entry (edit with visudo):
     youruser ALL=(root) NOPASSWD: /usr/sbin/iptables, /usr/sbin/ip6tables, /sbin/nft
   - Replace paths with the correct locations for your system.

5) Optional: Persisting rules
   - If the project supports persistence (file or DB), ensure the configured storage path is writable by the service user. Check project config files for persistence settings.

## Usage (Running)
Note: modifying firewall rules requires elevated privileges. Use caution.

1) Find the application entrypoint in the repository (common names: app.py, server.py, run.py). Example commands below assume app.py exists.

2) Run locally for development
   - Activate virtualenv (if not already): source .venv/bin/activate
   - Start the app:
     python app.py
   - Or, if using Flask CLI and the app is in app.py:
     export FLASK_APP=app.py
     flask run --host=127.0.0.1 --port=5000
   - Access the UI at http://localhost:5000

3) Run with system-level privileges (if your app calls iptables/nft directly)
   - Run the app with sudo (example):
     sudo python app.py
   - Or run as a service under a system user with sudoers rules configured for the firewall commands (preferred over running the web server as root).

4) Production deployment suggestions
   - Use a WSGI server such as gunicorn and put it behind a reverse proxy (nginx).
   - Keep the web server process running as an unprivileged user; use helper scripts invoked with sudo for firewall changes.
   - Example systemd service snippet (replace ExecStart and user/group as appropriate):
     [Unit]
     Description=Local-firewall service
     After=network.target

     [Service]
     User=localfw
     Group=localfw
     WorkingDirectory=/path/to/Local-firewall
     ExecStart=/path/to/.venv/bin/gunicorn -b 127.0.0.1:8000 app:app
     Restart=on-failure

     [Install]
     WantedBy=multi-user.target

5) CLI examples (adjust to actual scripts in this repo)
   - Add rule: python manage_rules.py add --ip 1.2.3.4 --action block
   - List rules: python manage_rules.py list

6) Stopping the service
   - If running in foreground: Ctrl+C
   - If running as systemd: sudo systemctl stop local-firewall

## Configuration
- Review and update configuration files (if any) under the repo root or a config/ directory.
- Ensure the service runs with necessary privileges to modify firewall rules (may require sudo/root or properly-configured sudoers entries).

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
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
Maintainer: @vivekrautela56