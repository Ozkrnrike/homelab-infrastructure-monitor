"""
SQLAlchemy models for the monitoring system.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Enum, Text, ForeignKey, Index, BigInteger, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMPTZ
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class HostStatus(str, enum.Enum):
    """Host status enumeration."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(str, enum.Enum):
    """Alert severity enumeration."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Host(Base):
    """Host table - represents a monitored host."""

    __tablename__ = "hosts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    hostname = Column(String(255), nullable=False)
    api_key_hash = Column(String(255), nullable=False)
    status = Column(Enum(HostStatus), default=HostStatus.UNKNOWN, nullable=False)
    last_seen = Column(TIMESTAMPTZ, nullable=True)
    created_at = Column(TIMESTAMPTZ, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMPTZ, server_default=func.now(), onupdate=func.now())
    metadata = Column(JSONB, default={})

    # Relationships
    metrics = relationship("Metric", back_populates="host", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="host", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_hosts_status', 'status'),
        Index('ix_hosts_last_seen', 'last_seen'),
    )

    def __repr__(self):
        return f"<Host(id={self.id}, name='{self.name}', status={self.status})>"


class Metric(Base):
    """Metric table - stores time-series metrics data."""

    __tablename__ = "metrics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    host_id = Column(UUID(as_uuid=True), ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(TIMESTAMPTZ, nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # cpu, memory, disk, network, etc.
    metric_data = Column(JSONB, nullable=False)

    # Relationships
    host = relationship("Host", back_populates="metrics")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('ix_metrics_host_timestamp', 'host_id', 'timestamp'),
        Index('ix_metrics_type_timestamp', 'metric_type', 'timestamp'),
        Index('ix_metrics_host_type_timestamp', 'host_id', 'metric_type', 'timestamp'),
    )

    def __repr__(self):
        return f"<Metric(id={self.id}, host_id={self.host_id}, type='{self.metric_type}')>"


class AlertRule(Base):
    """Alert rules table - defines alerting conditions."""

    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    host_id = Column(UUID(as_uuid=True), ForeignKey("hosts.id", ondelete="CASCADE"), nullable=True)
    metric_type = Column(String(50), nullable=False)
    condition = Column(JSONB, nullable=False)  # Condition definition (e.g., {"cpu.percent": {"gt": 90}})
    severity = Column(Enum(AlertSeverity), nullable=False)
    duration_seconds = Column(Integer, default=0)  # How long condition must be true
    enabled = Column(String(10), default="true")
    notification_channels = Column(JSONB, default=[])  # List of notification channels
    created_at = Column(TIMESTAMPTZ, server_default=func.now())
    updated_at = Column(TIMESTAMPTZ, server_default=func.now(), onupdate=func.now())

    # Relationships
    alerts = relationship("Alert", back_populates="rule")

    def __repr__(self):
        return f"<AlertRule(id={self.id}, name='{self.name}', severity={self.severity})>"


class Alert(Base):
    """Alerts table - stores triggered alerts."""

    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    host_id = Column(UUID(as_uuid=True), ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True)
    severity = Column(Enum(AlertSeverity), nullable=False)
    message = Column(Text, nullable=False)
    triggered_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())
    resolved_at = Column(TIMESTAMPTZ, nullable=True)
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_at = Column(TIMESTAMPTZ, nullable=True)
    metadata = Column(JSONB, default={})

    # Relationships
    host = relationship("Host", back_populates="alerts")
    rule = relationship("AlertRule", back_populates="alerts")

    # Indexes
    __table_args__ = (
        Index('ix_alerts_host_triggered', 'host_id', 'triggered_at'),
        Index('ix_alerts_severity', 'severity'),
        Index('ix_alerts_resolved', 'resolved_at'),
    )

    def __repr__(self):
        return f"<Alert(id={self.id}, severity={self.severity}, resolved={self.resolved_at is not None})>"


class ApiKey(Base):
    """API Keys table - stores API keys for authentication."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_type = Column(String(50), nullable=False)  # agent, user, admin
    host_id = Column(UUID(as_uuid=True), ForeignKey("hosts.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(TIMESTAMPTZ, server_default=func.now())
    last_used_at = Column(TIMESTAMPTZ, nullable=True)
    expires_at = Column(TIMESTAMPTZ, nullable=True)
    revoked = Column(String(10), default="false")
    metadata = Column(JSONB, default={})

    # Indexes
    __table_args__ = (
        Index('ix_api_keys_key_hash', 'key_hash'),
    )

    def __repr__(self):
        return f"<ApiKey(id={self.id}, name='{self.name}', type='{self.key_type}')>"
