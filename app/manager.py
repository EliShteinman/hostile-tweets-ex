# app/manager.py
import logging
from typing import List, Dict, Any
from .processor import DataProcessor

logger = logging.getLogger(__name__)


class AnalysisManager:
    """Class for managing analysis and processing tasks"""

    def __init__(self, data: dict):
        logger.info("Starting AnalysisManager setup")

        self.raw_data = data['raw_data']
        self.data_as_df = None
        self.path_weapons = "data/weapons.txt"
        self.weapons = self._load_weapons()
        self.processor = DataProcessor()

        logger.info(f"Received {len(self.raw_data)} records for processing")
        logger.info(f"Loaded {len(self.weapons)} weapons from blacklist")

    def start_analysis(self):
        """Start full analysis process"""
        logger.info("Starting full analysis process...")

        try:
            # Convert to DataFrame
            logger.info("Step 1: Convert to DataFrame")
            self.data_as_df = DataProcessor().convert_to_df(self.raw_data)

            if self.data_as_df.empty:
                logger.error("DataFrame is empty - cannot continue analysis")
                return

            # Process rare words
            logger.info("Step 2: Find rare words")
            self.data_as_df["rarest_word"] = self.data_as_df["Text"].apply(
                self.processor.find_first_rarest_word
            )
            rare_words_found = self.data_as_df["rarest_word"].apply(lambda x: x != "").sum()
            logger.info(f"Found rare words in {rare_words_found} records")

            # Detect weapons
            logger.info("Step 3: Detect weapons")
            self.data_as_df["weapons_detected"] = self.data_as_df["Text"].apply(
                lambda txt: self.processor.find_weapons(txt, self.weapons)
            )
            weapons_found = self.data_as_df["weapons_detected"].apply(lambda x: x != "").sum()
            logger.info(f"Found weapons in {weapons_found} records")

            # Analyze sentiment
            logger.info("Step 4: Analyze sentiment")
            self.data_as_df["sentiment"] = self.data_as_df["Text"].apply(
                self.processor.get_sentiment
            )

            # Sentiment statistics with clearer logging
            sentiment_stats = self.data_as_df["sentiment"].value_counts()
            logger.info("Sentiment analysis completed")
            logger.info(f"Positive sentiment: {sentiment_stats.get('positive', 0)} records")
            logger.info(f"Negative sentiment: {sentiment_stats.get('negative', 0)} records")
            logger.info(f"Neutral sentiment: {sentiment_stats.get('neutral', 0)} records")

            # Change column name and fix id field
            logger.info("Step 5: Rename columns for output format")
            self.data_as_df = self.data_as_df.rename(columns={
                "Text": "original_text",
                "_id": "id"
            })

            logger.info("Analysis process completed successfully")
            logger.info(f"Summary: {len(self.data_as_df)} processed records with {len(self.data_as_df.columns)} fields")

        except Exception as e:
            logger.error(f"Error in analysis process: {e}")
            raise

    def get_processed_data(self) -> List[Dict[str, Any]]:
        """Return processed data as list of dictionaries"""
        logger.info("Preparing processed data for output...")

        if self.data_as_df is None:
            logger.error("No processed data - need to run start_analysis() first")
            return []

        try:
            result = self.data_as_df.to_dict("records")
            logger.info(f"Successfully prepared {len(result)} processed records for output")
            return result
        except Exception as e:
            logger.error(f"Error preparing output data: {e}")
            return []

    def _load_weapons(self) -> set:
        """Load weapons list from file"""
        logger.info(f"Loading weapons list from: {self.path_weapons}")

        try:
            with open(self.path_weapons, "r", encoding="utf-8") as f:
                weapons = {line.strip() for line in f if line.strip()}

            logger.info(f"Successfully loaded {len(weapons)} weapons from blacklist")

            # Log sample weapons for verification
            if weapons:
                sample_weapons = list(weapons)[:3]
                logger.debug(f"Sample weapons loaded: {sample_weapons}")

            return weapons

        except FileNotFoundError:
            logger.error(f"Weapons file not found: {self.path_weapons}")
            logger.error("Analysis will continue without weapon detection")
            return set()
        except Exception as e:
            logger.error(f"Error loading weapons file: {e}")
            return set()