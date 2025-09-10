# Imports for core functionality
from flask import Flask, render_template, request, redirect, session, Response, jsonify, url_for, flash
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash
import time
import os
import json
import subprocess
import logging
import re

# Set up logging for the Flask app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- Security Configuration ---

# 1. CSRF Protection
csrf = CSRFProtect(app)

# 2. Secret Key Management
# Load the secret key from an environment variable for production
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key:
    logging.warning("FLASK_SECRET_KEY is not set. Using a default, insecure key for development.")
    app.secret_key = "your_default_secret_key_for_dev_12345"

# 3. User Authentication
# In a production environment, use a database to store user credentials with hashed passwords.
# For this example, we use environment variables for simplicity and security.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

if not ADMIN_PASSWORD_HASH:
    logging.warning("ADMIN_PASSWORD_HASH is not set. Using a default, insecure password.")
    # In a real app, you would set this hash via a setup script, not hardcode the password.
    ADMIN_PASSWORD_HASH = generate_password_hash("password123")

def check_credentials(username, password):
    """Securely checks credentials against environment variables."""
    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
        return True
    return False

# --- Utility Functions ---

def is_valid_ip(ip):
    """Validates an IP address format."""
    # Regex for a valid IPv4 address
    if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip):
        return True
    return False

def generate_logs():
    """Generator for streaming live logs via Server-Sent Events (SSE)."""
    try:
        with open("firewall.log", "r") as file:
            file.seek(0, 2)  # Go to the end of the file
            while True:
                line = file.readline()
                if not line:
                    time.sleep(1)
                    continue
                yield f"data: {line.strip()}\n\n"
    except FileNotFoundError:
        logging.error("firewall.log not found. Cannot stream logs.")
        yield "data: [ERROR] firewall.log not found.\n\n"

# --- Routes ---

@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login and session management."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if check_credentials(username, password):
            session["user"] = username
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid Credentials", "error")
            return render_template("login.html", error="Invalid Credentials")
    return render_template("login.html")

@app.route("/")
def index():
    """Main dashboard page."""
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/logs")
def logs():
    """Endpoint for streaming logs."""
    if "user" not in session:
        return Response("Unauthorized", status=401)
    return Response(generate_logs(), mimetype="text/event-stream")

@app.route("/logout")
def logout():
    """Handles user logout."""
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/blocked_ips")
def blocked_ips():
    """Page to view and unblock IP addresses."""
    if "user" not in session:
        return redirect(url_for("login"))
    try:
        with open("blocked_ips.txt", "r") as f:
            ips = f.read().splitlines()
    except FileNotFoundError:
        ips = []
    return render_template("blocked_ips.html", ips=ips)

@app.route("/unblock/<ip>")
def unblock(ip):
    """Unblocks a specific IP address after validation."""
    if "user" not in session:
        return redirect(url_for("login"))
    
    if not is_valid_ip(ip):
        flash(f"Invalid IP address format: {ip}", "error")
        return redirect(url_for("blocked_ips"))

    unblock_ip(ip)
    flash(f"IP {ip} has been unblocked.", "success")
    return redirect(url_for("blocked_ips"))

def unblock_ip(ip):
    """Removes an IP from the block list and from iptables securely."""
    try:
        # Find the rule number for the given IP
        result = subprocess.run(
            ["sudo", "iptables", "-L", "INPUT", "-n", "--line-numbers"],
            capture_output=True, text=True, check=True
        )
        lines = result.stdout.splitlines()
        rule_num_to_delete = None

        for line in lines:
            if ip in line and "DROP" in line:
                rule_num_to_delete = line.split()[0]
                break
        
        if rule_num_to_delete:
            # Securely delete the rule by its number
            subprocess.run(
                ["sudo", "iptables", "-D", "INPUT", rule_num_to_delete],
                check=True
            )
            logging.info(f"iptables rule for {ip} deleted.")
        else:
            logging.warning(f"No active iptables DROP rule found for {ip}.")

    except FileNotFoundError:
        logging.error("'sudo' or 'iptables' command not found.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing iptables command: {e.stderr}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while unblocking {ip}: {e}")

    # Update the blocked_ips.txt file
    try:
        with open("blocked_ips.txt", "r") as f:
            entries = f.readlines()
        with open("blocked_ips.txt", "w") as f:
            for entry in entries:
                if entry.strip() != ip:
                    f.write(entry)
        logging.info(f"IP {ip} removed from blocked_ips.txt.")
    except FileNotFoundError:
        logging.error("blocked_ips.txt not found during unblock attempt.")

@app.route("/clear_logs")
def clear_logs():
    """Clears the firewall log files."""
    if "user" not in session:
        return redirect(url_for("login"))
    try:
        # Securely clear files
        with open("firewall.log", "w") as f1, open("maplog.json", "w") as f2:
            pass
        flash("Firewall logs cleared successfully.", "success")
    except IOError as e:
        flash(f"Error clearing logs: {e}", "error")
        logging.error(f"Error clearing logs: {e}")
    return redirect(url_for("index"))

@app.route("/mapdata")
def map_data():
    """Provides GeoIP data for the map as a JSON array."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = []
    try:
        with open("maplog.json", "r") as f:
            for line in f:
                if line.strip(): # Avoid decoding empty lines
                    data.append(json.loads(line.strip()))
    except FileNotFoundError:
        logging.warning("maplog.json not found. Returning empty data.")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from maplog.json: {e}")
        
    return jsonify(data)

if __name__ == "__main__":
    # Use environment variable to control debug mode
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
