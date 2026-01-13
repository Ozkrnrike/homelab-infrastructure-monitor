"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.models.models import HostStatus, AlertSeverity


# ============================================================================
# Host Schemas
# ============================================================================

class HostBase(BaseModel):
    """Base host schema."""
    name: str = Field(..., min_length=1, max_length=255)
    hostname: str = Field(..., min_length=1, max_length=255)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HostCreate(HostBase):
    """Schema for creating a new host."""
    api_key: Optional[str] = None  # If not provided, one will be generated


class HostUpdate(BaseModel):
    """Schema for updating a host."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[HostStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class Host(HostBase):
    """Schema for host response."""
    id: UUID
    status: HostStatus
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class HostWithKey(Host):
    """Schema for host response with API key (only on creation)."""
    api_key: str


# ============================================================================
# Metric Schemas
# ============================================================================

class MetricBase(BaseModel):
    """Base metric schema."""
    timestamp: datetime
    metric_type: str = Field(..., min_length=1, max_length=50)
    metric_data: Dict[str, Any]


class MetricCreate(MetricBase):
    """Schema for creating a new metric."""
    host_id: UUID


class Metric(MetricBase):
    """Schema for metric response."""
    id: int
    host_id: UUID

    model_config = ConfigDict(from_attributes=True)


class MetricPayload(BaseModel):
    """Schema for metric payload from agent."""
    timestamp: datetime
    system: Dict[str, Any]
    metrics: Dict[str, Any]
    containers: List[Dict[str, Any]] = Field(default_factory=list)
    health_checks: List[Dict[str, Any]] = Field(default_factory=list)


class MetricQuery(BaseModel):
    """Schema for querying metrics."""
    host_id: Optional[UUID] = None
    metric_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    aggregation: Optional[str] = Field(None, pattern="^(none|avg|min|max|sum)$")
    interval: Optional[str] = Field(None, pattern="^(1m|5m|15m|1h|6h|1d)$")
    limit: int = Field(default=1000, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


# ============================================================================
# Alert Schemas
# ============================================================================

class AlertRuleBase(BaseModel):
    """Base alert rule schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    metric_type: str = Field(..., min_length=1, max_length=50)
    condition: Dict[str, Any]
    severity: AlertSeverity
    duration_seconds: int = Field(default=0, ge=0)
    enabled: bool = True
    notification_channels: List[str] = Field(default_factory=list)


class AlertRuleCreate(AlertRuleBase):
    """Schema for creating an alert rule."""
    host_id: Optional[UUID] = None


class AlertRuleUpdate(BaseModel):
    """Schema for updating an alert rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None
    severity: Optional[AlertSeverity] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    enabled: Optional[bool] = None
    notification_channels: Optional[List[str]] = None


class AlertRule(AlertRuleBase):
    """Schema for alert rule response."""
    id: UUID
    host_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AlertBase(BaseModel):
    """Base alert schema."""
    severity: AlertSeverity
    message: str


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    host_id: UUID
    rule_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Alert(AlertBase):
    """Schema for alert response."""
    id: UUID
    host_id: UUID
    rule_id: Optional[UUID] = None
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class AlertAcknowledge(BaseModel):
    """Schema for acknowledging an alert."""
    acknowledged_by: str = Field(..., min_length=1, max_length=255)


# ============================================================================
# Response Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool


# ============================================================================
# WebSocket Schemas
# ============================================================================

class WSMessage(BaseModel):
    """WebSocket message schema."""
    type: str
    data: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)
