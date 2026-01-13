"""
Hosts API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import logging

from app.db.base import get_db
from app.models.models import Host
from app.schemas.schemas import Host as HostSchema, HostCreate, HostUpdate, HostWithKey
from app.core.auth import hash_api_key, generate_api_key

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=List[HostSchema])
async def list_hosts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all registered hosts."""
    query = select(Host).offset(skip).limit(limit)
    result = await db.execute(query)
    hosts = result.scalars().all()
    return hosts


@router.post("", response_model=HostWithKey, status_code=status.HTTP_201_CREATED)
async def create_host(
    host_create: HostCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new host and generate API key."""
    # Check if host with this name already exists
    existing = await db.execute(
        select(Host).where(Host.name == host_create.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Host with name '{host_create.name}' already exists"
        )

    # Generate API key
    api_key = host_create.api_key or generate_api_key()
    api_key_hash = hash_api_key(api_key)

    # Create host
    host = Host(
        name=host_create.name,
        hostname=host_create.hostname,
        api_key_hash=api_key_hash,
        metadata=host_create.metadata
    )

    db.add(host)
    await db.commit()
    await db.refresh(host)

    logger.info(f"Host created: {host.name} (ID: {host.id})")

    # Return host with API key (only time it's shown)
    return HostWithKey(
        **host.__dict__,
        api_key=api_key
    )


@router.get("/{host_id}", response_model=HostSchema)
async def get_host(
    host_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get host details by ID."""
    result = await db.execute(
        select(Host).where(Host.id == host_id)
    )
    host = result.scalar_one_or_none()

    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found"
        )

    return host


@router.put("/{host_id}", response_model=HostSchema)
async def update_host(
    host_id: UUID,
    host_update: HostUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update host metadata."""
    result = await db.execute(
        select(Host).where(Host.id == host_id)
    )
    host = result.scalar_one_or_none()

    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found"
        )

    # Update fields
    if host_update.name is not None:
        host.name = host_update.name
    if host_update.hostname is not None:
        host.hostname = host_update.hostname
    if host_update.status is not None:
        host.status = host_update.status
    if host_update.metadata is not None:
        host.metadata = host_update.metadata

    await db.commit()
    await db.refresh(host)

    logger.info(f"Host updated: {host.name}")

    return host


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(
    host_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a host and all its metrics."""
    result = await db.execute(
        select(Host).where(Host.id == host_id)
    )
    host = result.scalar_one_or_none()

    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found"
        )

    await db.delete(host)
    await db.commit()

    logger.info(f"Host deleted: {host.name}")

    return None
