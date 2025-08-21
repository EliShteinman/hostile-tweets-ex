import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from .dependencies import data_loader

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    מנהל אירועי התחלה וסיום של האפליקציה.
    """
    # בהתחלת השרת:
    logger.info("Application startup: connecting to database...")
    try:
        await data_loader.connect()
        logger.info("Database connection established successfully.")
        df = await data_loader.get_all_data_as_dataframe()
        logger.info(f"Successfully retrieved {len(df)} raw records")

    except Exception as e:
        logger.error(
            f"Application startup failed: Could not connect to the database. Error: {e}"
        )

    yield

    # בסגירת השרת:
    logger.info("Application shutdown: disconnecting from database...")
    try:
        data_loader.disconnect()
        logger.info("Database disconnection completed.")
    except Exception as e:
        logger.error(f"Error during database disconnection: {e}")


# יצירת אפליקציית FastAPI הראשית
app = FastAPI(
    lifespan=lifespan,
    title="Malicious Text Analysis API",
    version="1.0.0",
    description="מערכת לניתוח טקסטים זדוניים - זיהוי רגש, מילים נדירות וכלי נשק",
)


@app.get("/")
def health_check_endpoint():
    """
    בדיקת בריאות בסיסית.
    משמש לבדיקות readiness ו-liveness של OpenShift.
    """
    return {
        "status": "ok",
        "service": "Malicious Text Analysis API",
        "version": "1.0.0",
    }


@app.get("/health")
def detailed_health_check():
    """
    בדיקת בריאות מפורטת.
    מחזירה 503 אם מסד הנתונים לא זמין.
    """
    db_status = "connected" if data_loader.collection is not None else "disconnected"

    if db_status == "disconnected":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    return {
        "status": "ok",
        "service": "Malicious Text Analysis API",
        "version": "1.0.0",
        "database_status": db_status,
    }


@app.get("/data")
async def read_raw_data():
    """
    מחזיר את הנתונים הגולמיים מהמסד נתונים ללא עיבוד.
    שימושי לדיבוג ובדיקת החיבור למסד הנתונים.
    """
    try:
        logger.info("Retrieving raw data from database")
        raw_data = await data_loader.get_all_data()
        logger.info(f"Successfully retrieved {len(raw_data)} raw records")
        return raw_data
    except RuntimeError as e:
        logger.error(f"Database error retrieving raw data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving raw data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
