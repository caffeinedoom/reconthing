# ReconThing

> The tool is currently in development. For any questions or ideas, feel free to contact me at **sam@pluckware.com**.

<div align="center">

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com/)

An automated web reconnaissance tool that delivers your essential tools directly through Discord for effortless access.

## Demo
<kbd>
  <a href="https://vimeo.com/1031346565">
    <img 
      src="https://vumbnail.com/1031346565.jpg" 
      alt="ReconThing Demo"
      width="500"
    />
  </a>
</kbd>
</div>


---

Current Tooling Support (on-development):
- [subfinder](https://github.com/projectdiscovery/subfinder)
- [dnsx](https://github.com/projectdiscovery/dnsx)
- [httpx](https://github.com/projectdiscovery/httpx)


<div align="center">

[Installation](#installation) •
[Features](#features) •
[Usage](#usage) •
[Documentation](#documentation)

</div>

---

## Table of Contents

1. [Features](#features)
   - [Core Capabilities](#core-capabilities)
   - [Interfaces](#interfaces)
   - [Data Management](#data-management)
   - [Deployment](#deployment)

2. [Tested Environment](#tested-environment)

3. [Prerequisites](#prerequisites)
   - [Ubuntu Installation](#for-ubuntu-installation-of-prerequisites)

4. [Installation](#installation)
   - [Initial Setup](#initial-setup)
   - [Deployment Methods](#choose-your-deployment-method)
   - [Verification](#verification)

5. [Usage](#usage)
   - [Discord Bot Commands](#discord-bot-commands)
   - [Command Flags](#command-flags)

6. [Environment Variables](#environment-variables)


8. [Contact](#contact)

---

## Features

**Core Capabilities**
- Automated subdomain enumeration using subfinder
- DNS resolution with dnsx integration
- HTTP/HTTPS service probing using httpx
- Comprehensive reconnaissance workflow

**Interfaces**
- Discord bot for easy command execution
- RESTful API for programmatic access
- Interactive command-line interface

**Data Management**
- PostgreSQL database for result persistence
- CSV export capabilities
- Efficient data retrieval system

**Deployment**
- Docker Compose support
- Easy configuration via environment variables
- Scalable architecture

---

## Tested Environment

<div align="center">

[![Ubuntu](https://img.shields.io/badge/Ubuntu%2020.04%20VPS-Tested%20&%20Verified-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com/)

</div>

## Prerequisites

Before you begin, ensure you have:

- Python 3.11 or higher installed
- PostgreSQL 15 or higher installed
- Docker and Docker Compose installed
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- Git installed (for cloning the repository)

For **Ubuntu** installation of prerequisites:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## Installation

### Initial Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/reconthing.git
   cd reconthing
   ```

2. **Choose Your Environment File**
   ```bash
   # For Docker deployment
   cp .env.docker.example .env.docker
   # For local deployment
   cp .env.local.example .env.local
   ```

3. **Configure Your Environment Variables**
   Edit your chosen .env file and fill in the required values:
   ```ini
   DB_USER=your_db_user
   DB_PASSWORD=your_secure_password
   DB_HOST=db             # Use 'db' for Docker, 'localhost' for local
   DB_NAME=your_db_name
   API_HOST=api          # Use 'api' for Docker, 'localhost' for local
   API_PORT=8000
   DISCORD_BOT_TOKEN=your_discord_bot_token
   ```

### Choose Your Deployment Method

<details>
<summary><b>🐋 Docker Deployment</b></summary>

1. **Start the Services**
   ```bash
   docker-compose up -d
   ```

2. **Verify All Services are Running**
   ```bash
   docker-compose ps
   ```

3. **Check the Logs**
   ```bash
   # View all logs
   docker-compose logs -f
   
   # View specific service logs
   docker-compose logs -f api        # For API logs
   docker-compose logs -f discord_bot # For Discord bot logs
   docker-compose logs -f db         # For Database logs
   ```

4. **Stopping the Services**
   ```bash
   docker-compose down
   ```
</details>

<details>
<summary><b>💻 Local Environment</b></summary>

1. **Set up Python Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate    # Windows
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Required Tools**
   ```bash
   # Install Go
   wget https://golang.org/dl/go1.21.6.linux-amd64.tar.gz
   sudo tar -C /usr/local -xzf go1.21.6.linux-amd64.tar.gz
   export PATH=$PATH:/usr/local/go/bin

   # Install reconnaissance tools
   go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
   go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
   go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
   ```

4. **Configure PostgreSQL**
   ```bash
   # Start PostgreSQL service
   sudo systemctl start postgresql
   sudo systemctl enable postgresql

   # Create database and user
   sudo -u postgres psql -c "CREATE DATABASE your_db_name;"
   sudo -u postgres psql -c "CREATE USER your_db_user WITH PASSWORD 'your_password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;"
   ```

5. **Start the Services**
   ```bash
   # Terminal 1: Start the API
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

   # Terminal 2: Start the Discord Bot
   python -m bot.bot
   ```

6. **Verify Installation**
   - API should be accessible at: http://localhost:8000
   - Discord bot should show as online in your Discord server
   - Check the logs in the `logs` directory
</details>

### Verification

After either deployment method, verify your installation:

1. **API Health Check**
   ```bash
   curl http://localhost:8000
   # Should return: {"message":"Welcome to Reconthing API"}
   ```

2. **Discord Bot**
   - Send `!help` in your Discord server
   - Bot should respond with available commands

3. **Check Logs**
   - Look for any errors in the `logs/bbrf.log` file
   - All services should be running without errors

If you encounter any issues during installation, please check the [Troubleshooting](#troubleshooting) section or open an issue on GitHub.

---

## Usage

### Discord Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!help` | Show available commands | `!help` |
| `!basicrecon` | Full reconnaissance | `!basicrecon example.com` |
| `!subdomain` | Enumerate subdomains | `!subdomain example.com` |
| `!getsubdomain` | Retrieve subdomains | `!getsubdomain example.com` |
| `!dns` | DNS resolution | `!dns example.com` |
| `!getdns` | Get DNS results | `!getdns example.com` |
| `!http` | HTTP probing | `!http example.com` |
| `!gethttp` | Get HTTP results | `!gethttp example.com` |

### Command Flags

| Flag | Description |
|------|-------------|
| `-csv` | Export results in CSV format |
| `-all` | Include all available data (DNS queries) |

---


### Environment Variables

<details>

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_USER` | Database username | - |
| `DB_PASSWORD` | Database password | - |
| `DB_HOST` | Database host | `localhost` |
| `DB_NAME` | Database name | - |
| `API_HOST` | API host | `localhost` |
| `API_PORT` | API port | `8000` |
| `DISCORD_BOT_TOKEN` | Discord bot token | - |

</details>


---


## Contact

Sam Paredes - [@caffeinedoom](https://twitter.com/affeinedoom)

Project Link -  [reconthing.com](https://reconthing.com)

---

<div align="center">
Made with passion by Sam Paredes
</div>