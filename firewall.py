import subprocess
import sys
import os
import logging
from datetime import datetime
from collections import defaultdict, deque
import json

# Check for Scapy and other dependencies
try:
    from scapy.all import sniff, IP, TCP, UDP
    import geoip2.database
except ImportError as e:
    print(f"A required library is missing: {e}.")
    print("Please install the required libraries using:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Configuration
LOG_FILE = "firewall.log"
BLOCKED_IPS_FILE = "blocked_ips.txt"
THRESHOLD = 100  # packet threshold per 5 seconds
TIME_WINDOW = 5 # seconds
MONITORED_PORTS = {22: "SSH", 80: "HTTP", 443: "HTTPS", 53: "DNS"}
DEFAULT_INTERFACE = "eth0" # Default network interface

# GeoIP setup
try:
    geo_reader = geoip2.database.Reader("GeoLite2-City.mmdb")
except geoip2.errors.FileNotFoundError:
    print("[ERROR] GeoLite2-City.mmdb not found. GeoIP functionality will be disabled.")
    geo_reader = None

# Track activity
ip_activity = defaultdict(lambda: deque(maxlen=THRESHOLD * 2))
blocked_ips = set()
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_blocked_ips():
    """Load blocked IPs from file into a set for fast lookup."""
    global blocked_ips
    if os.path.exists(BLOCKED_IPS_FILE):
        with open(BLOCKED_IPS_FILE, "r") as f:
            blocked_ips = set(line.strip() for line in f)

def is_blocked(ip):
    """Checks if an IP is in the blocked_ips set."""
    return ip in blocked_ips

def block_ip(ip):
    """Adds an IP to the block list and applies the iptables rule."""
    if not is_blocked(ip):
        blocked_ips.add(ip)
        with open(BLOCKED_IPS_FILE, "a") as f:
            f.write(ip + "\n")
        try:
            # Securely call iptables using a list of arguments
            subprocess.run(["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"], check=True, capture_output=True, text=True)
            logging.warning(f"Rate limit exceeded by {ip} - BLOCKED.")
        except subprocess.CalledProcessError as e:
            logging.error(f"iptables block failed for {ip}: {e.stderr}")
        except FileNotFoundError:
            logging.error("iptables command not found. Make sure it's in the system's PATH.")

def get_geo_info(ip):
    """Fetches geographical information for an IP."""
    if not geo_reader:
        return "Unknown Location"
    try:
        response = geo_reader.city(ip)
        country = response.country.name or "Unknown"
        city = response.city.name or "Unknown"
        return f"{city}, {country}"
    except geoip2.errors.AddressNotFoundError:
        return "Unknown Location (Private IP)"
    except Exception as e:
        logging.error(f"GeoIP lookup failed for {ip}: {e}")
        return "Unknown Location"

class PacketProcessor:
    def __init__(self, interface):
        self.interface = interface

    def packet_callback(self, packet):
        """Processes each packet captured by Scapy."""
        if IP not in packet:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        src_ip = packet[IP].src

        if is_blocked(src_ip):
            return

        dst_ip = packet[IP].dst
        geo_info = get_geo_info(src_ip)
        proto = None
        port_info = ""
        alert = False

        if TCP in packet:
            proto = "TCP"
            sport, dport = packet[TCP].sport, packet[TCP].dport
        elif UDP in packet:
            proto = "UDP"
            sport, dport = packet[UDP].sport, packet[UDP].dport
        else:
            return

        if dport in MONITORED_PORTS:
            alert = True
            port_info = f"{MONITORED_PORTS[dport]} (Port {dport})"

        log_entry = {
            "timestamp": timestamp,
            "src": src_ip,
            "dst": dst_ip,
            "proto": proto,
            "geo": geo_info,
            "alert": port_info if alert else None
        }

        with open("maplog.json", "a") as mapfile:
            mapfile.write(json.dumps(log_entry) + "\n")

        log_message = f"{proto} | Src: {src_ip} ({geo_info}) -> Dst: {dst_ip}"
        if alert:
            log_message += f" [ALERT: {port_info}]"
            logging.warning(log_message)
        else:
            logging.info(log_message)

        # Rate limiting logic
        now = datetime.now().timestamp()
        ip_activity[src_ip].append(now)
        
        # Clean up old timestamps
        while ip_activity[src_ip] and now - ip_activity[src_ip][0] > TIME_WINDOW:
            ip_activity[src_ip].popleft()

        if len(ip_activity[src_ip]) > THRESHOLD:
            block_ip(src_ip)

    def start_sniffing(self):
        """Starts the packet sniffing process."""
        print(f"Starting packet sniffing on interface '{self.interface}'...")
        try:
            sniff(prn=self.packet_callback, store=False, iface=self.interface, filter="ip")
        except OSError as e:
            print(f"Error starting sniffing on interface '{self.interface}': {e}")
            print("Please make sure the interface exists and you have the necessary permissions.")
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred during sniffing: {e}")
            sys.exit(1)

def main():
    """Main function to run the firewall."""
    if os.geteuid() != 0:
        print("This script must be run as root. Please use 'sudo python3 firewall.py'")
        sys.exit(1)

    if not geo_reader:
        print("Please download GeoLite2-City.mmdb from MaxMind and place it in the same directory.")
        sys.exit(1)

    load_blocked_ips()

    interface = os.getenv("NETWORK_INTERFACE", DEFAULT_INTERFACE)
    processor = PacketProcessor(interface)
    processor.start_sniffing()

if __name__ == "__main__":
    main()

