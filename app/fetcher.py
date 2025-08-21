import logging
from typing import Any, Dict, List, Optional

import pandas as pd
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
            self.client = AsyncMongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=30000,
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
        """Retrieves all documents as a list of dictionaries. Raises RuntimeError if not connected."""
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        try:
            logger.info("Attempting to retrieve all records")
            items: List[Dict[str, Any]] = []
            async for item in self.collection.find({}):
                item["_id"] = str(item["_id"])
                items.append(item)
            logger.info(f"Retrieved {len(items)} records from database.")
            return items
        except PyMongoError as e:
            logger.error(f"Error retrieving all data: {e}")
            raise RuntimeError(f"Database operation failed: {e}")

    async def get_all_data_as_dataframe(self) -> pd.DataFrame:
        """
        Retrieves all documents and returns them as a pandas DataFrame.
        More efficient for data processing operations.
        Raises RuntimeError if not connected.
        """
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        try:
            logger.info("Attempting to retrieve all records as DataFrame")
            items: List[Dict[str, Any]] = []

            # Step 1: Collect all documents
            async for item in self.collection.find({}):
                item["_id"] = str(item["_id"])
                items.append(item)

            # Step 2: Convert to DataFrame
            if items:
                df = pd.DataFrame(items)
                logger.info(f"Retrieved and converted {len(df)} records to DataFrame.")
                return df
            else:
                logger.info("No records found, returning empty DataFrame.")
                return pd.DataFrame()

        except PyMongoError as e:
            logger.error(f"Error retrieving data as DataFrame: {e}")
            raise RuntimeError(f"Database operation failed: {e}")
        except Exception as e:
            logger.error(f"Error converting data to DataFrame: {e}")
            raise RuntimeError(f"DataFrame conversion failed: {e}")

    async def get_data_count(self) -> int:
        """
        Returns the number of documents in the collection.
        Useful for checking data availability without loading everything.
        """
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        try:
            count = await self.collection.count_documents({})
            logger.info(f"Collection contains {count} documents")
            return count
        except PyMongoError as e:
            logger.error(f"Error counting documents: {e}")
            raise RuntimeError(f"Count operation failed: {e}")

    async def get_sample_document(self) -> Optional[Dict[str, Any]]:
        """
        Returns one sample document for schema inspection.
        Useful for debugging and understanding data structure.
        """
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        try:
            sample = await self.collection.find_one({})
            if sample:
                sample["_id"] = str(sample["_id"])
                logger.info("Retrieved sample document")
                return sample
            else:
                logger.info("No documents found in collection")
                return None
        except PyMongoError as e:
            logger.error(f"Error retrieving sample document: {e}")
            raise RuntimeError(f"Sample retrieval failed: {e}")
