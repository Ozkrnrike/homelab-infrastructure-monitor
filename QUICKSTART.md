# HomeLab Infrastructure Monitor - Quick Start

Get up and running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Python 3.11+ (for agent)
- Port 8000 and 5432 available

## Step 1: Clone and Configure (1 minute)

```bash
cd "HomeLab Infrastructure Monitor"

# Create environment file
cp .env.example .env

# Generate secure keys
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "API_KEY_SALT=$(openssl rand -hex 32)" >> .env
```

## Step 2: Start Backend (2 minutes)

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy (30 seconds)
docker-compose ps

# Initialize database and create sample host
python scripts/init_db.py --seed
```

**Save the API keys printed by the init script!**

Example output:
```
✓ Sample host created: sample-server
  Host ID: 123e4567-e89b-12d3-a456-426614174000
  Agent API Key: abc123xyz...

✓ Admin API key created
  Admin API Key: def456uvw...
```

## Step 3: Verify Backend (1 minute)

```bash
# Check API health
curl http://localhost:8000/health

# View API docs in browser
open http://localhost:8000/docs

# Test authentication
curl -X GET http://localhost:8000/api/v1/hosts \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY"
```

## Step 4: Start Monitoring Agent (1 minute)

```bash
cd agent

# Create virtual environment (first time only)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Set your API key from Step 2
export AGENT_API_KEY="your-agent-api-key-here"

# Update config.yaml with correct server URL if needed
# (Default is http://localhost:8000/api/v1)

# Start agent
python agent.py
```

You should see:
```
2026-01-13 10:30:00 - agent - INFO - Agent initialized successfully
2026-01-13 10:30:00 - agent - INFO - Starting agent loop (interval: 30s)
2026-01-13 10:30:01 - agent - INFO - Metrics sent successfully (status: 201)
```

## Step 5: View Your Metrics

### Using API

```bash
# Get latest metrics for all hosts
curl http://localhost:8000/api/v1/metrics/latest \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" | jq

# Query specific host metrics
curl "http://localhost:8000/api/v1/metrics?host_id=YOUR_HOST_ID&limit=10" \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" | jq
```

### Using Swagger UI

1. Open http://localhost:8000/docs
2. Click "Authorize" button
3. Enter: `Bearer YOUR_ADMIN_API_KEY`
4. Try the endpoints!

## What's Next?

### Add More Hosts

```bash
curl -X POST http://localhost:8000/api/v1/hosts \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "production-server",
    "hostname": "prod.example.com",
    "metadata": {"environment": "production"}
  }'
```

Save the returned API key and deploy the agent to that host!

### Deploy Agent as Service (Linux)

```bash
# Copy to /opt
sudo cp -r agent /opt/homelab-monitor-agent

# Create systemd service
sudo nano /etc/systemd/system/homelab-monitor.service
```

Paste:
```ini
[Unit]
Description=HomeLab Monitor Agent
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/opt/homelab-monitor-agent
Environment="AGENT_API_KEY=your-key-here"
ExecStart=/opt/homelab-monitor-agent/venv/bin/python agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable homelab-monitor
sudo systemctl start homelab-monitor
sudo systemctl status homelab-monitor
```

### Build Frontend (Next Phase)

The frontend is not yet built. To create it:

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm run dev
```

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed next steps.

## Troubleshooting

### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker-compose ps db

# View logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Agent Can't Connect
```bash
# Test network connectivity
curl http://localhost:8000/health

# Check API key is set
echo $AGENT_API_KEY

# Run agent with verbose logging
python agent.py -v
```

### Port Already in Use
```bash
# Find what's using port 8000
lsof -i :8000

# Change port in docker-compose.yml
# Edit: ports: - "8001:8000"  # Changed from 8000
docker-compose up -d
```

## Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f db

# Restart a service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove data
docker-compose down -v  # WARNING: Deletes database!

# Access database directly
docker-compose exec db psql -U homelab -d homelab_monitor

# View hosts in database
docker-compose exec db psql -U homelab -d homelab_monitor -c "SELECT name, status, last_seen FROM hosts;"
```

## Default Ports

- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **PostgreSQL:** localhost:5432
- **Frontend:** (Not yet built - will be :3000)

## Documentation

- **Full Setup Guide:** [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)
- **Project Status:** [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Architecture:** [README.md](README.md)
- **API Reference:** http://localhost:8000/docs (when running)

## Support

If you encounter issues:

1. Check [SETUP_GUIDE.md](docs/SETUP_GUIDE.md) troubleshooting section
2. Review logs: `docker-compose logs`
3. Verify environment variables: `cat .env`
4. Ensure ports are available
5. Check Docker is running: `docker ps`

---

**Ready to monitor!** 🎉

Your HomeLab Infrastructure Monitor is now collecting metrics. Access the API at http://localhost:8000/docs to explore your data.
