import logging
import certifi
from typing import Any, Dict, List, Optional

from pymongo import AsyncMongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError

logger = logging.getLogger(__name__)


class DataLoader:
    """
    This class is our MongoDB expert.
    It receives connection details from an external source and is not
    directly dependent on environment variables.
    """

    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client: Optional[AsyncMongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None

    async def connect(self):
        """Creates an asynchronous connection to MongoDB and sets up indexes if needed."""
        try:
            ca_file = certifi.where()

            self.client = AsyncMongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=30000,
                tls=True,
                tlsCAFile=ca_file
            )
            await self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.info("Successfully connected to MongoDB.")
        except (PyMongoError, ConnectionFailure) as e:
            logger.error(f"DATABASE CONNECTION FAILED: {e}")
            self.client = None
            self.db = None
            self.collection = None
            raise e

    def disconnect(self):
        """Closes the connection to the database."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB.")

    async def get_all_data(self) -> List[Dict[str, Any]]:
        """Retrieves all documents. Raises RuntimeError if not connected."""
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        try:
            logger.info("Attempting to retrieve all soldiers")
            items: List[Dict[str, Any]] = []
            async for item in self.collection.find({}):
                item["_id"] = str(item["_id"])
                items.append(item)
            logger.info(f"Retrieved {len(items)} soldiers from database.")
            return items
        except PyMongoError as e:
            logger.error(f"Error retrieving all data: {e}")
            raise RuntimeError(f"Database operation failed: {e}")