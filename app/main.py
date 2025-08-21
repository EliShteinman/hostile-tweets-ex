import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from .manager import AnalysisManager
from .dependencies import data_loader

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# משתנה גלובלי לתוצאות מעובדות
processed_results = None
startup_error = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """מנהל אירועי התחלה וסיום של האפליקציה."""
    global processed_results, startup_error

    # בהתחלת השרת:
    logger.info("Application startup: connecting to database...")
    try:
        await data_loader.connect()
        logger.info("Database connection established successfully.")

        # קבלת נתונים
        logger.info("Loading data from database...")
        df = await data_loader.get_all_data_as_dataframe()
        logger.info(f"Successfully retrieved {len(df)} raw records")

        # דיבוג סכמת הנתונים
        logger.info(f"DataFrame columns: {list(df.columns)}")

        # יצירת מנהל הניתוח
        logger.info("Creating AnalysisManager...")
        analysis_manager = AnalysisManager(df)

        # הרצת הניתוח - זה קורה רק פעם אחת!
        logger.info("Starting one-time analysis processing...")
        analysis_manager.run_full_analysis()

        # שמירת התוצאות בזיכרון
        processed_results = analysis_manager.get_processed_data()
        logger.info(f"Analysis completed! {len(processed_results)} records processed and cached")

        if processed_results and len(processed_results) > 0:
            logger.info(f"Sample processed record: {processed_results[0]}")

        startup_error = None

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        startup_error = str(e)
        processed_results = []

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
    """בדיקת בריאות בסיסית."""
    return {
        "status": "ok",
        "service": "Malicious Text Analysis API",
        "version": "1.0.0",
    }


@app.get("/health")
def detailed_health_check():
    """בדיקת בריאות מפורטת."""
    db_status = "connected" if data_loader.collection is not None else "disconnected"

    # בדיקת מצב העיבוד
    if startup_error:
        processing_status = f"failed: {startup_error}"
    elif processed_results is not None:
        processing_status = f"ready ({len(processed_results)} records)"
    else:
        processing_status = "not_ready"

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
        "processing_status": processing_status,
    }


@app.get("/data")
async def read_raw_data():
    """מחזיר את הנתונים הגולמיים מהמסד נתונים ללא עיבוד."""
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


@app.get("/processed-data")
async def get_processed_data():
    """
    הנקודת קצה הראשית - מחזירה נתונים מעובדים בפורמט הנדרש.
    הנתונים מעובדים מראש ונשמרים בזיכרון!
    """
    global processed_results, startup_error

    # בדיקה אם יש שגיאה מהstartup
    if startup_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Analysis failed during startup: {startup_error}"
        )

    # בדיקה אם התוצאות מוכנות
    if processed_results is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analysis results not ready yet. Please wait for startup to complete."
        )

    try:
        logger.info(f"Returning cached processed data - {len(processed_results)} records")
        return processed_results

    except Exception as e:
        logger.error(f"Error returning processed data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while returning data"
        )


@app.get("/stats")
async def get_stats():
    """מחזיר סטטיסטיקות על המערכת"""
    global processed_results, startup_error

    return {
        "total_processed_records": len(processed_results) if processed_results else 0,
        "startup_error": startup_error,
        "status": "ready" if processed_results else "not_ready",
        "database_connected": data_loader.collection is not None
    }


@app.get("/debug/schema")
async def debug_schema():
    """endpoint לדיבוג סכמת הנתונים"""
    try:
        # קבלת דגימה מהDB
        df = await data_loader.get_all_data_as_dataframe()

        return {
            "columns": list(df.columns),
            "dataframe_shape": df.shape,
            "sample_record": df.iloc[0].to_dict() if not df.empty else None
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/debug/weapons")
def debug_weapons():
    """endpoint לבדיקת רשימת הנשקים"""
    try:
        from .processor import DataProcessor
        processor = DataProcessor()
        return {
            "weapons_count": len(processor.weapons_list),
            "sample_weapons": list(processor.weapons_list)[:10] if processor.weapons_list else [],
            "weapons_file_loaded": len(processor.weapons_list) > 0
        }
    except Exception as e:
        return {"error": str(e)}
