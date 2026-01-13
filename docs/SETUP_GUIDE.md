# HomeLab Infrastructure Monitor - Setup Guide

This guide will walk you through setting up the HomeLab Infrastructure Monitor from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Manual Setup](#manual-setup)
4. [Configuration](#configuration)
5. [Database Initialization](#database-initialization)
6. [Agent Deployment](#agent-deployment)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Python** 3.11+ (for agent and local development)
- **Node.js** 18+ and **npm** (for frontend development)
- **PostgreSQL** 15+ (if running without Docker)

### Optional

- **Git** (for version control)
- **Make** (for convenience commands)

## Quick Start (Docker)

The fastest way to get started is using Docker Compose:

### 1. Clone the Repository

```bash
git clone <repository-url>
cd HomeLab\ Infrastructure\ Monitor
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and update at minimum:
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `API_KEY_SALT` - Generate with: `openssl rand -hex 32`

### 3. Start Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- Backend API on port 8000
- Frontend dashboard on port 3000

### 4. Initialize Database

```bash
# Access the backend container
docker-compose exec backend bash

# Run database migrations
alembic upgrade head

# Create initial admin API key (inside container)
python scripts/create_api_key.py --name "Admin" --type admin

# Exit container
exit
```

### 5. Create Your First Host

```bash
# Use the API to register a host
curl -X POST http://localhost:8000/api/v1/hosts \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-server",
    "hostname": "server.local",
    "metadata": {"location": "home-lab"}
  }'

# Save the returned API key for the agent!
```

### 6. Deploy Agent

On the machine you want to monitor:

```bash
# Copy agent files
scp -r agent/ user@your-server:/opt/homelab-monitor-agent/

# SSH into the server
ssh user@your-server

# Install dependencies
cd /opt/homelab-monitor-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure agent
nano config.yaml
# Update server.url and server.api_key

# Run agent
python agent.py
```

### 7. Access Dashboard

Open your browser: `http://localhost:3000`

## Manual Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example ../.env
# Edit .env with your settings

# Start PostgreSQL (if not using Docker)
# On macOS: brew services start postgresql@15
# On Ubuntu: sudo systemctl start postgresql

# Create database
createdb homelab_monitor

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Update VITE_API_URL if needed

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

### Agent Setup

```bash
cd agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp config.yaml.example config.yaml
nano config.yaml

# Set API key in environment
export AGENT_API_KEY="your-agent-api-key-here"

# Run agent
python agent.py

# Or with verbose logging
python agent.py -v
```

## Configuration

### Backend Configuration

Edit `backend/app/core/config.py` or set environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/homelab_monitor

# Security
SECRET_KEY=your-secret-key
API_KEY_SALT=your-salt

# Application
ENVIRONMENT=development  # development, staging, production
METRICS_RETENTION_DAYS=30
```

### Agent Configuration

Edit `agent/config.yaml`:

```yaml
server:
  url: http://your-server:8000/api/v1
  api_key: ${AGENT_API_KEY}

collection:
  interval_seconds: 30
  include_docker: true
  disk_mounts:
    - /
    - /home

health_checks:
  - name: nginx
    type: http
    url: http://localhost:80
    expected_status: 200
```

### Frontend Configuration

Edit `frontend/.env.local`:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Database Initialization

### Using Alembic Migrations

```bash
cd backend

# Create initial migration (first time only)
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head

# Rollback (if needed)
alembic downgrade -1
```

### Manual Database Setup

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE homelab_monitor;

-- Create user
CREATE USER homelab WITH PASSWORD 'homelab';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE homelab_monitor TO homelab;

-- Connect to database
\c homelab_monitor

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO homelab;
```

## Agent Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/homelab-monitor-agent.service`:

```ini
[Unit]
Description=HomeLab Monitor Agent
After=network.target

[Service]
Type=simple
User=homelab
WorkingDirectory=/opt/homelab-monitor-agent
Environment="AGENT_API_KEY=your-api-key-here"
ExecStart=/opt/homelab-monitor-agent/venv/bin/python agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable homelab-monitor-agent
sudo systemctl start homelab-monitor-agent
sudo systemctl status homelab-monitor-agent
```

### Cron Job (Alternative)

```bash
# Edit crontab
crontab -e

# Add entry (runs agent continuously)
@reboot cd /opt/homelab-monitor-agent && /opt/homelab-monitor-agent/venv/bin/python agent.py >> /var/log/homelab-agent.log 2>&1
```

### Docker Container (Agent)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY agent.py config.yaml ./

CMD ["python", "agent.py"]
```

Build and run:

```bash
docker build -t homelab-agent .
docker run -d --name agent \
  -e AGENT_API_KEY=your-key \
  -v /:/hostroot:ro \
  --privileged \
  homelab-agent
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps db
# or
sudo systemctl status postgresql

# Check connection
psql -U homelab -d homelab_monitor -h localhost

# View logs
docker-compose logs db
```

### Backend Not Starting

```bash
# Check logs
docker-compose logs backend

# Verify environment variables
docker-compose exec backend env | grep DATABASE_URL

# Test database connection
docker-compose exec backend python -c "from app.db.base import engine; print('Connection OK')"
```

### Agent Cannot Connect

```bash
# Test network connectivity
curl -v http://your-server:8000/health

# Verify API key
curl -X POST http://your-server:8000/api/v1/metrics \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Check agent logs
python agent.py -v
```

### Frontend Build Issues

```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+

# Build manually
npm run build
```

## Next Steps

1. **Secure Your Installation**
   - Change default passwords
   - Enable HTTPS (see [SSL_SETUP.md](SSL_SETUP.md))
   - Configure firewall rules

2. **Set Up Monitoring**
   - Deploy agents to all hosts
   - Configure health checks
   - Set up alert rules

3. **Customize**
   - Adjust retention policies
   - Configure alert channels
   - Customize dashboard

4. **Production Deployment**
   - See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
   - Enable authentication
   - Set up backups

## Support

For issues and questions:
- Check the [FAQ](FAQ.md)
- Review [API Documentation](http://localhost:8000/docs)
- Open an issue on GitHub
