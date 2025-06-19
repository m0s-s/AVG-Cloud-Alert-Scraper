# AVG Cloud Alert Scraper

This Python script automates the collection of security alerts from the AVG Business API, enriching each alert with full device information. Each alert is saved in a separate `.txt` file containing a single-line JSON object. The script is cross-platform and keeps track of the last collected alert to avoid duplicates.

## 🔧 Features

- Retrieves all alerts using AVG's public API
- Enriches each alert with complete device metadata (hostname, IP, OS, etc.)
- Avoids re-downloading alerts using `createdOn` timestamp tracking
- Fully compatible with both Windows and Linux systems
- Handles API rate limiting (HTTP 429)
- Logs are written as one-line JSON per file, ready for further parsing or ingestion

## 📁 File Structure

```
C:/avgcloud or /opt/avgcloud/
├── logs/
│   ├── ALERTNAME_alertid_timestamp.txt
├── last_created_on.txt
```

Each `.txt` file contains:
```json
{
  "alert_data": {...},
  "device_info": {...}
}
```

## ⚙️ Requirements

- Python 3.8 or higher
- `requests`
- `python-dateutil`

Install dependencies:
```bash
pip install requests python-dateutil
```

## 🛠️ Setup

Before running the script, edit the configuration section to include your AVG API credentials:

```python
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
```

## ▶️ Usage

To run the script:
```bash
python avg_alert_scraper.py
```

What it does:
- Authenticates using the provided API credentials
- Retrieves the company ID
- Fetches all available alerts
- Enriches them with device information
- Saves each result as a flat JSON `.txt` file

The script will only download new alerts on subsequent runs.

## 🐧 Linux Notes

On Linux systems, logs are saved under `/opt/avgcloud`. You may need to run the script with elevated privileges:

```bash
sudo python avg_alert_scraper.py
```

## 🚧 Roadmap

Planned future improvements include:

- Native syslog forwarding for SIEM ingestion
- Filtering alerts by category or severity
- Automated packaging and scheduling

## 🛡️ Disclaimer

This tool is provided as-is, without official support from AVG or Avast. Use it responsibly and at your own risk.

## 📬 Contact

For questions, issues, or contributions, please open an issue on the GitHub repository.
