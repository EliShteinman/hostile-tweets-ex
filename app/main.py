# app/main.py
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from .dependencies import data_loader
from .manager import AnalysisManager

# Setup logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Global data storage
data: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events"""

    # Server startup
    logger.info("Starting application setup...")

    try:
        # Step 1: Connect to database
        logger.info("Step 1: Connecting to database...")
        await data_loader.connect()
        logger.info("Database connection completed")

        # Step 2: Get data
        logger.info("Step 2: Getting data from database...")
        raw_data = await data_loader.get_all_data()
        data['raw_data'] = raw_data
        logger.info(f"Got {len(raw_data)} records from database")

        # Step 3: Process data
        logger.info("Step 3: Starting data processing...")
        analysis_manager = AnalysisManager(data)
        analysis_manager.start_analysis()
        data['processed_data'] = analysis_manager.get_processed_data()
        logger.info(f"Processed {len(data['processed_data'])} records")

        logger.info("Application setup completed successfully")

    except Exception as e:
        logger.error(f"Application setup failed: {e}")
        logger.error("Application will continue running but without data")
        data['raw_data'] = []
        data['processed_data'] = []

    # Run application
    yield

    # Server shutdown
    logger.info("Starting application shutdown...")
    try:
        data_loader.disconnect()
        logger.info("Database disconnection completed")
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    lifespan=lifespan,
    title="Malicious Text Analysis API",
    version="1.0.0",
    description="System for analyzing malicious texts - emotion detection, rare words and weapons",
)

logger.info("FastAPI initialized - Malicious Text Analysis Application")


@app.get("/")
def health_check_endpoint():
    """Basic health check"""
    logger.info("Basic health check request")

    response = {
        "status": "ok",
        "service": "Malicious Text Analysis API",
        "version": "1.0.0",
        "message": "Service is running"
    }

    logger.debug(f"Health response: {response['status']}")
    return response


@app.get("/health")
def detailed_health_check():
    """Detailed health check"""
    logger.info("Detailed health check request")

    # Check database status
    db_status = "connected" if data_loader.collection is not None else "disconnected"
    logger.debug(f"Database status: {db_status}")

    # Check data availability
    data_status = {
        "raw_records": len(data.get('raw_data', [])),
        "processed_records": len(data.get('processed_data', []))
    }
    logger.debug(f"Data status: {data_status}")

    if db_status == "disconnected":
        logger.warning("Database is not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    response = {
        "status": "healthy",
        "service": "Malicious Text Analysis API",
        "version": "1.0.0",
        "database_status": db_status,
        "data_status": data_status,
        "timestamp": "2025-01-01T00:00:00Z"
    }

    logger.info("Detailed health check completed successfully")
    return response


@app.get("/data")
async def read_raw_data():
    """Return raw data from database without processing"""
    logger.info("Request for raw data")

    try:
        raw_data = await data_loader.get_all_data()
        logger.info(f"Returned {len(raw_data)} raw records")
        return raw_data

    except RuntimeError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@app.get("/data-proses")
def read_processed_data():
    """Return processed data"""
    logger.info("Request for processed data")

    processed_data = data.get('processed_data', [])

    if not processed_data:
        logger.warning("No processed data available")
        return []

    logger.info(f"Returning {len(processed_data)} processed records")
    return processed_data