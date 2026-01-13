#!/usr/bin/env python3
"""
Database initialization script.
Creates initial database schema and optionally seeds with sample data.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.db.base import Base
from app.models.models import Host, Metric, Alert, AlertRule, ApiKey
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database tables."""
    logger.info(f"Connecting to database: {settings.DATABASE_URL}")

    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    try:
        async with engine.begin() as conn:
            logger.info("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✓ Tables created successfully!")

        logger.info("Database initialization complete!")
        return True

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

    finally:
        await engine.dispose()


async def seed_sample_data():
    """Seed database with sample data for testing."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from app.core.auth import hash_api_key, generate_api_key
    from datetime import datetime, timezone

    logger.info("Seeding sample data...")

    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        try:
            # Create sample host
            api_key = generate_api_key()
            sample_host = Host(
                name="sample-server",
                hostname="server.local",
                api_key_hash=hash_api_key(api_key),
                status="unknown",
                metadata={"location": "home-lab", "description": "Sample monitoring host"}
            )
            session.add(sample_host)

            # Create admin API key
            admin_key = generate_api_key()
            admin_api_key = ApiKey(
                name="Admin Key",
                key_hash=hash_api_key(admin_key),
                key_type="admin",
                metadata={"created_by": "init_script"}
            )
            session.add(admin_api_key)

            await session.commit()
            await session.refresh(sample_host)

            logger.info(f"✓ Sample host created: {sample_host.name}")
            logger.info(f"  Host ID: {sample_host.id}")
            logger.info(f"  Agent API Key: {api_key}")
            logger.info(f"")
            logger.info(f"✓ Admin API key created")
            logger.info(f"  Admin API Key: {admin_key}")
            logger.info(f"")
            logger.info(f"Save these keys! They won't be shown again.")

        except Exception as e:
            logger.error(f"Error seeding data: {e}")
            await session.rollback()

        finally:
            await engine.dispose()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Initialize HomeLab Monitor database")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed database with sample data"
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables first (WARNING: destructive!)"
    )

    args = parser.parse_args()

    if args.drop:
        response = input("⚠️  This will DROP all existing tables. Are you sure? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Aborted.")
            return

        async def drop_tables():
            engine = create_async_engine(settings.DATABASE_URL)
            async with engine.begin() as conn:
                logger.info("Dropping tables...")
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("✓ Tables dropped")
            await engine.dispose()

        asyncio.run(drop_tables())

    # Initialize database
    success = asyncio.run(init_database())

    if success and args.seed:
        asyncio.run(seed_sample_data())


if __name__ == "__main__":
    main()
