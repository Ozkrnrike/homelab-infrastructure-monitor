"""
Metrics API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List
from datetime import datetime, timedelta
import logging

from app.db.base import get_db
from app.models.models import Metric, Host
from app.schemas.schemas import MetricPayload, Metric as MetricSchema, MetricQuery
from app.core.auth import get_current_host

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", status_code=status.HTTP_201_CREATED)
async def ingest_metrics(
    payload: MetricPayload,
    db: AsyncSession = Depends(get_db),
    current_host: Host = Depends(get_current_host)
):
    """
    Ingest metrics from an agent.
    Requires agent API key authentication.
    """
    try:
        # Update host's last_seen timestamp
        current_host.last_seen = datetime.utcnow()

        # Store different metric types
        metric_types = {
            "cpu": payload.metrics.get("cpu", {}),
            "memory": payload.metrics.get("memory", {}),
            "disks": payload.metrics.get("disks", []),
            "disk_io": payload.metrics.get("disk_io", {}),
            "network": payload.metrics.get("network", {})
        }

        # Create metric records
        for metric_type, metric_data in metric_types.items():
            if metric_data:
                metric = Metric(
                    host_id=current_host.id,
                    timestamp=payload.timestamp,
                    metric_type=metric_type,
                    metric_data=metric_data
                )
                db.add(metric)

        # Store system info as a separate metric type
        if payload.system:
            system_metric = Metric(
                host_id=current_host.id,
                timestamp=payload.timestamp,
                metric_type="system",
                metric_data=payload.system
            )
            db.add(system_metric)

        # Store container metrics
        if payload.containers:
            container_metric = Metric(
                host_id=current_host.id,
                timestamp=payload.timestamp,
                metric_type="containers",
                metric_data={"containers": payload.containers}
            )
            db.add(container_metric)

        # Store health checks
        if payload.health_checks:
            health_metric = Metric(
                host_id=current_host.id,
                timestamp=payload.timestamp,
                metric_type="health_checks",
                metric_data={"checks": payload.health_checks}
            )
            db.add(health_metric)

        await db.commit()

        logger.info(f"Metrics ingested successfully for host {current_host.name}")

        return {"message": "Metrics ingested successfully", "host_id": str(current_host.id)}

    except Exception as e:
        logger.error(f"Error ingesting metrics: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest metrics"
        )


@router.get("", response_model=List[MetricSchema])
async def query_metrics(
    host_id: str = None,
    metric_type: str = None,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 1000,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Query historical metrics with filters.
    Supports filtering by host, metric type, and time range.
    """
    try:
        # Build query
        query = select(Metric)
        conditions = []

        if host_id:
            conditions.append(Metric.host_id == host_id)

        if metric_type:
            conditions.append(Metric.metric_type == metric_type)

        if start_time:
            conditions.append(Metric.timestamp >= start_time)

        if end_time:
            conditions.append(Metric.timestamp <= end_time)
        elif not start_time:
            # Default to last 24 hours if no time range specified
            conditions.append(Metric.timestamp >= datetime.utcnow() - timedelta(hours=24))

        if conditions:
            query = query.where(and_(*conditions))

        # Order by timestamp descending
        query = query.order_by(Metric.timestamp.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        metrics = result.scalars().all()

        return metrics

    except Exception as e:
        logger.error(f"Error querying metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query metrics"
        )


@router.get("/latest")
async def get_latest_metrics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get the latest metrics for all hosts.
    Returns the most recent metric of each type for each host.
    """
    try:
        # Query to get latest metrics per host and metric type
        # This is a simplified version - in production, you'd use window functions
        query = select(Host).where(Host.status != "unknown")
        result = await db.execute(query)
        hosts = result.scalars().all()

        latest_metrics = []

        for host in hosts:
            # Get latest metric for this host
            metric_query = (
                select(Metric)
                .where(Metric.host_id == host.id)
                .order_by(Metric.timestamp.desc())
                .limit(10)
            )
            metric_result = await db.execute(metric_query)
            host_metrics = metric_result.scalars().all()

            if host_metrics:
                latest_metrics.append({
                    "host_id": str(host.id),
                    "host_name": host.name,
                    "status": host.status,
                    "last_seen": host.last_seen,
                    "metrics": [
                        {
                            "type": m.metric_type,
                            "timestamp": m.timestamp,
                            "data": m.metric_data
                        }
                        for m in host_metrics
                    ]
                })

        return latest_metrics

    except Exception as e:
        logger.error(f"Error getting latest metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get latest metrics"
        )


@router.delete("/cleanup")
async def cleanup_old_metrics(
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    Clean up metrics older than specified days.
    Admin endpoint for maintenance.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Delete old metrics
        delete_query = Metric.__table__.delete().where(Metric.timestamp < cutoff_date)
        result = await db.execute(delete_query)
        await db.commit()

        deleted_count = result.rowcount

        logger.info(f"Deleted {deleted_count} old metrics (older than {days} days)")

        return {
            "message": f"Deleted {deleted_count} metrics older than {days} days",
            "cutoff_date": cutoff_date
        }

    except Exception as e:
        logger.error(f"Error cleaning up metrics: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup metrics"
        )
