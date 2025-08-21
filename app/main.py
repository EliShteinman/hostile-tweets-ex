import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from .dependencies import data_loader

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    """
    # On server startup:
    logger.info("Application startup: connecting to database...")
    try:
        await data_loader.connect()
        logger.info("Database connection established successfully.")
    except Exception as e:
        logger.error(f"Application startup failed: Could not connect to the database. Error: {e}")

    yield

    # On server shutdown:
    logger.info("Application shutdown: disconnecting from database...")
    try:
        data_loader.disconnect()
        logger.info("Database disconnection completed.")
    except Exception as e:
        logger.error(f"Error during database disconnection: {e}")


# Create the main FastAPI application instance
app = FastAPI(
    lifespan=lifespan,
    title="FastAPI MongoDB Service",
    version="2.0",
    description="A microservice for managing soldier data, deployed on OpenShift.",
)

@app.get("/")
def health_check_endpoint():
    """
    Health check endpoint.
    Used by OpenShift's readiness and liveness probes.
    """
    return {"status": "ok", "service": "FastAPI MongoDB CRUD Service"}


@app.get("/health")
def detailed_health_check():
    """
    Detailed health check endpoint.
    Returns 503 if database is not available.
    """
    db_status = "connected" if data_loader.collection is not None else "disconnected"

    if db_status == "disconnected":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    return {
        "status": "ok",
        "service": "FastAPI MongoDB CRUD Service",
        "version": "2.0",
        "database_status": db_status,
    }

@app.get("/data")
async def read_all_soldiers():
    """
    Retrieves all soldiers from the database.
    """
    try:
        logger.info("Attempting to retrieve all soldiers")
        tweets = await data_loader.get_all_data()
        logger.info(f"Successfully retrieved {len(tweets)} soldiers")
        return tweets
    except RuntimeError as e:
        logger.error(f"Database error retrieving all soldiers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving all soldiers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )