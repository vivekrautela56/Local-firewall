import requests
import tarfile
import shutil
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_and_extract_geoip_database():
    """Downloads and extracts the GeoLite2-City database from MaxMind."""
    maxmind_key = os.getenv("MAXMIND_KEY")
    if not maxmind_key or maxmind_key == "YOUR_MAXMIND_LICENSE_KEY":
        logging.error("MAXMIND_KEY not found or not set in .env file. Please add your MaxMind license key to the .env file.")
        return

    url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={maxmind_key}&suffix=tar.gz"
    
    try:
        logging.info("Downloading GeoLite2-City database...")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open("GeoLite2-City.tar.gz", "wb") as f:
            f.write(response.content)
        logging.info("Download complete.")

        logging.info("Extracting database...")
        with tarfile.open("GeoLite2-City.tar.gz", "r:gz") as tar:
            # Secure extraction to prevent directory traversal
            for member in tar.getmembers():
                if member.name.endswith("GeoLite2-City.mmdb"):
                    member.name = os.path.basename(member.name) # Extract only the filename
                    tar.extract(member, path=".")
                    logging.info(f"Extracted {member.name}")
                    break
            else:
                logging.error("GeoLite2-City.mmdb not found in the archive.")
                return

        # Move the database to the desired location
        db_path = "GeoLite2-City.mmdb"
        if os.path.exists(db_path):
            # The file is already in the correct location, no need to move
            logging.info("GeoLite2 database saved as GeoLite2-City.mmdb")
        else:
            logging.error("DB file not found after extraction.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Download failed: {e}")
    except tarfile.TarError as e:
        logging.error(f"Extraction failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        # Clean up downloaded and extracted files
        if os.path.exists("GeoLite2-City.tar.gz"):
            os.remove("GeoLite2-City.tar.gz")

if __name__ == "__main__":
    download_and_extract_geoip_database()
