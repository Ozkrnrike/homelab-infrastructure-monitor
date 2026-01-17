# HomeLab Infrastructure Monitor

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-20.10+-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**A production-ready, real-time infrastructure monitoring dashboard for home lab environments**

[Features](#-features) • [Tech Stack](#-tech-stack) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API](#-api-documentation)

</div>

---

## Overview

HomeLab Infrastructure Monitor is a **full-stack, three-tier web application** that provides comprehensive monitoring for servers, containers, and services. Built to demonstrate real-world DevOps, SysAdmin, and full-stack development skills.

<div align="center">
<img src="docs/dashboard-preview.png" alt="Dashboard Preview" width="800"/>
</div>

## Features

| Feature | Description |
|---------|-------------|
| **Real-Time Monitoring** | Live CPU, memory, disk, and network metrics with WebSocket streaming |
| **Docker Integration** | Container status, resource usage, and health monitoring |
| **Service Health Checks** | HTTP endpoints, TCP ports, and process monitoring |
| **Smart Alerting** | Configurable thresholds with cooldown periods to prevent alert fatigue |
| **Historical Analytics** | Time-series data storage with trend visualization |
| **Multi-Host Support** | Monitor unlimited machines from a single dashboard |
| **RESTful API** | Full API for integration with other tools and automation |

---

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.11+** | Core language |
| **FastAPI** | Modern async web framework |
| **SQLAlchemy 2.0** | Async ORM with type hints |
| **PostgreSQL 15** | Time-series data storage with JSONB |
| **Alembic** | Database migrations |
| **Pydantic v2** | Data validation |
| **WebSockets** | Real-time streaming |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **TypeScript** | Type-safe JavaScript |
| **Vite** | Fast build tool |
| **TailwindCSS** | Utility-first styling |
| **Recharts** | Data visualization |
| **React Query** | Server state management |
| **React Router** | Client-side routing |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **Nginx** | Reverse proxy (production) |
| **psutil** | System metrics collection |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MONITORED HOSTS                                    │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐           │
│  │  Agent   │     │  Agent   │     │  Agent   │     │  Agent   │           │
│  │ (Python) │     │ (Python) │     │ (Python) │     │ (Python) │           │
│  └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘           │
└───────┼────────────────┼────────────────┼────────────────┼──────────────────┘
        │                │                │                │
        │         HTTPS POST /api/v1/metrics               │
        └────────────────┴────────────────┴────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CENTRAL SERVER                                     │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        FastAPI Backend                              │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │    │
│  │  │   Metrics   │  │    Hosts    │  │   Alerts    │  │ WebSocket │ │    │
│  │  │     API     │  │     API     │  │     API     │  │  Server   │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │    │
│  │                           │                                        │    │
│  │                    ┌──────┴───────┐                               │    │
│  │                    │ Alert Engine │                               │    │
│  │                    └──────────────┘                               │    │
│  └────────────────────────────┬───────────────────────────────────────┘    │
│                               │                                             │
│                               ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     PostgreSQL Database                             │    │
│  │   hosts │ metrics │ alerts │ alert_rules │ api_keys                │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                               │                                             │
│                               ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                       React Frontend                                │    │
│  │   Dashboard │ Hosts │ Metrics │ Alerts │ Services │ Settings       │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/homelab-monitor.git
cd homelab-monitor

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Access the dashboard
open http://localhost:3000
```

### Option 2: Development Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Agent (on each host to monitor):**
```bash
cd agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Edit config.yaml with your server URL and API key
python agent.py
```

---

## Project Structure

```
HomeLab Infrastructure Monitor/
├── agent/                      # Python collection agent
│   ├── agent.py               # Main agent with collectors
│   ├── config.yaml            # YAML configuration
│   └── requirements.txt       # psutil, requests, PyYAML
│
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # REST API endpoints
│   │   │   └── endpoints/     # metrics, hosts, alerts, websocket
│   │   ├── core/              # Config, auth, alert engine
│   │   ├── db/                # Database setup
│   │   ├── models/            # SQLAlchemy ORM models
│   │   └── schemas/           # Pydantic validation
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # React + TypeScript frontend
│   ├── src/
│   │   ├── api/               # API client
│   │   ├── components/        # Reusable components
│   │   │   ├── charts/        # CPU, Memory, Network charts
│   │   │   ├── layout/        # Sidebar, Header
│   │   │   └── ui/            # Card, Badge, Progress
│   │   ├── hooks/             # Custom React hooks
│   │   ├── lib/               # Utilities
│   │   ├── pages/             # Route pages
│   │   └── types/             # TypeScript definitions
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Environment template
└── README.md
```

---

## API Documentation

Once the backend is running, interactive documentation is available:

| Docs | URL |
|------|-----|
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **OpenAPI JSON** | http://localhost:8000/openapi.json |

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/metrics` | Ingest metrics (auth required) |
| `GET` | `/api/v1/metrics/latest` | Get latest metrics per host |
| `GET` | `/api/v1/hosts` | List all hosts |
| `POST` | `/api/v1/hosts` | Register new host |
| `GET` | `/api/v1/alerts` | List alerts |
| `POST` | `/api/v1/alerts/{id}/resolve` | Resolve an alert |
| `WS` | `/api/v1/ws/metrics` | Real-time metrics stream |

---

## Testing

```bash
# Backend unit tests
cd backend
pip install -r requirements.txt
pytest -v

# Frontend type checking
cd frontend
npm run build
```

---

## Skills Demonstrated

| Category | Skills |
|----------|--------|
| **Backend Development** | Python, FastAPI, REST APIs, WebSockets, async/await |
| **Frontend Development** | React, TypeScript, TailwindCSS, data visualization |
| **Database** | PostgreSQL, SQLAlchemy, database design, migrations |
| **DevOps** | Docker, Docker Compose, CI/CD, environment management |
| **System Administration** | Linux, process monitoring, networking, metrics collection |
| **Security** | API authentication, input validation, secure defaults |
| **Software Architecture** | Three-tier architecture, event-driven design, caching |

---

## Future Enhancements

- [ ] Kubernetes cluster monitoring
- [ ] Log aggregation with Elasticsearch
- [ ] Prometheus metrics export
- [ ] Slack/Discord alert notifications
- [ ] Custom dashboard builder
- [ ] Machine learning anomaly detection

---

## Contributing

This is a portfolio project demonstrating full-stack development skills. Feedback and suggestions are welcome!

---

## License

MIT License - feel free to use this as a reference or starting point for your own projects.

---

## Author

**Louis Sader**
Full-Stack Developer | DevOps Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/yourprofile)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github)](https://github.com/yourusername)

---

<div align="center">

**Built with modern technologies to demonstrate production-ready software engineering skills.**

</div>
