# HomeLab Infrastructure Monitor

A real-time system monitoring dashboard for home lab infrastructure, showcasing SysAdmin and DevOps skills.

## Overview

HomeLab Infrastructure Monitor is a three-tier web application that provides comprehensive monitoring for servers, containers, and services in home lab environments.

### Key Features

- Real-time CPU, memory, disk, and network utilization monitoring
- Docker container status and resource tracking
- Service health checks (HTTP endpoints, ports, processes)
- Historical data storage and trend visualization
- Configurable alerting thresholds with email/webhook notifications
- Multi-host support for monitoring multiple machines
- RESTful API for integration with other tools

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ MONITORED HOSTS                                                 │
│   [Agent.py] → [Agent.py] → [Agent.py]                         │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTPS POST /api/metrics
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ CENTRAL SERVER                                                  │
│   [FastAPI Backend] ←→ [PostgreSQL Database]                   │
│          │                                                       │
│          ▼ WebSocket                                            │
│   [React Frontend Dashboard]                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Collection Agent**: Python 3.11+, psutil, requests
- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL 15+
- **Frontend**: React 18+, TypeScript, TailwindCSS, Recharts
- **Deployment**: Docker, Docker Compose, Nginx
- **Optional**: Celery + Redis for background tasks

## Project Structure

```
HomeLab Infrastructure Monitor/
├── agent/                  # Collection agent
│   ├── agent.py           # Main agent script
│   ├── config.yaml        # Agent configuration
│   └── requirements.txt   # Python dependencies
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Configuration & auth
│   │   ├── db/           # Database setup
│   │   ├── models/       # SQLAlchemy models
│   │   └── schemas/      # Pydantic schemas
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── lib/          # Utilities
│   │   └── hooks/        # Custom hooks
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml     # Full stack deployment
└── docs/                  # Documentation
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Running with Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd HomeLab\ Infrastructure\ Monitor

# Start all services
docker-compose up -d

# Access the dashboard
open http://localhost:3000
```

### Development Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

#### Agent

```bash
cd agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python agent.py
```

## Configuration

### Agent Configuration

Edit `agent/config.yaml`:

```yaml
server:
  url: https://monitor.example.com/api
  api_key: ${AGENT_API_KEY}

collection:
  interval_seconds: 30
  include_docker: true
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
DATABASE_URL=postgresql://user:pass@localhost/homelab_monitor
SECRET_KEY=your-secret-key
API_KEY_SALT=your-salt
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Skills Demonstrated

- **Containerization**: Docker, Docker Compose
- **Backend Development**: Python, FastAPI, REST APIs
- **Database Management**: PostgreSQL, Time-Series Data
- **Infrastructure Monitoring**: Custom agents, Metrics collection
- **Frontend Development**: React, Real-time dashboards
- **Cloud Deployment**: AWS EC2, S3, CloudWatch
- **Infrastructure as Code**: Terraform, Docker Compose
- **Networking**: TCP/IP, HTTP/HTTPS, WebSockets

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Deployment

### Local Docker Deployment

```bash
docker-compose up -d
```

### AWS Deployment

See [docs/AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md) for detailed instructions.

## Future Enhancements

### Phase 2
- Kubernetes cluster monitoring
- Log aggregation and search
- Custom dashboard builder
- Multi-tenant support

### Phase 3
- Machine learning anomaly detection
- Capacity planning predictions
- Cost optimization recommendations

## Contributing

This is a portfolio project, but suggestions and feedback are welcome!

## License

MIT License

## Author

Louis Sader
January 2026

---

Built as a comprehensive demonstration of SysAdmin, DevOps, and Full-Stack Development skills.
