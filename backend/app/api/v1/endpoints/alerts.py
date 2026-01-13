"""
Alerts API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging

from app.db.base import get_db
from app.models.models import Alert, AlertRule
from app.schemas.schemas import (
    Alert as AlertSchema,
    AlertCreate,
    AlertAcknowledge,
    AlertRule as AlertRuleSchema,
    AlertRuleCreate,
    AlertRuleUpdate
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=List[AlertSchema])
async def list_alerts(
    host_id: Optional[UUID] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List alerts with optional filters.
    """
    query = select(Alert)

    # Apply filters
    if host_id:
        query = query.where(Alert.host_id == host_id)
    if severity:
        query = query.where(Alert.severity == severity)
    if resolved is not None:
        if resolved:
            query = query.where(Alert.resolved_at.isnot(None))
        else:
            query = query.where(Alert.resolved_at.is_(None))

    # Order by triggered_at descending
    query = query.order_by(Alert.triggered_at.desc())

    # Pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    alerts = result.scalars().all()

    return alerts


@router.post("/{alert_id}/acknowledge", response_model=AlertSchema)
async def acknowledge_alert(
    alert_id: UUID,
    ack: AlertAcknowledge,
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an alert."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )

    alert.acknowledged_by = ack.acknowledged_by
    alert.acknowledged_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    logger.info(f"Alert {alert_id} acknowledged by {ack.acknowledged_by}")

    return alert


@router.post("/{alert_id}/resolve", response_model=AlertSchema)
async def resolve_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Mark an alert as resolved."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )

    if alert.resolved_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already resolved"
        )

    alert.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    logger.info(f"Alert {alert_id} resolved")

    return alert


# Alert Rules endpoints
@router.get("/rules", response_model=List[AlertRuleSchema])
async def list_alert_rules(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all alert rules."""
    query = select(AlertRule).offset(skip).limit(limit)
    result = await db.execute(query)
    rules = result.scalars().all()
    return rules


@router.post("/rules", response_model=AlertRuleSchema, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    rule: AlertRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert rule."""
    alert_rule = AlertRule(**rule.dict())
    db.add(alert_rule)
    await db.commit()
    await db.refresh(alert_rule)

    logger.info(f"Alert rule created: {alert_rule.name}")

    return alert_rule


@router.put("/rules/{rule_id}", response_model=AlertRuleSchema)
async def update_alert_rule(
    rule_id: UUID,
    rule_update: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an alert rule."""
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule with ID {rule_id} not found"
        )

    # Update fields
    update_data = rule_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)

    logger.info(f"Alert rule updated: {rule.name}")

    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an alert rule."""
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule with ID {rule_id} not found"
        )

    await db.delete(rule)
    await db.commit()

    logger.info(f"Alert rule deleted: {rule.name}")

    return None
