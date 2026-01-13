"""
API v1 router.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import metrics, hosts, alerts

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
api_router.include_router(hosts.router, prefix="/hosts", tags=["Hosts"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
