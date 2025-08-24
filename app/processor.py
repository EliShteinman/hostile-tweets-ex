# app/processor.py
import logging
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter
from typing import List, Optional

logger = logging.getLogger(__name__)

# Download needed data
try:
    nltk.download("vader_lexicon", quiet=True)
    logger.info("VADER lexicon installed successfully")
except Exception as e:
    logger.error(f"Error installing VADER lexicon: {e}")

# Create one object for whole system
sid = SentimentIntensityAnalyzer()


class DataProcessor:
    """Class for processing and analyzing texts"""

    def __init__(self):
        logger.info("Starting DataProcessor setup")

    @staticmethod
    def convert_to_df(data: List[dict]) -> pd.DataFrame:
        """Convert data to pandas DataFrame"""
        logger.info(f"Starting conversion to DataFrame from {len(data)} records")

        if not data:
            logger.warning("No data received for conversion")
            return pd.DataFrame()

        try:
            df = pd.DataFrame(data)
            logger.info(f"Conversion completed successfully: {len(df)} rows, {len(df.columns)} columns")
            logger.debug(f"Columns: {list(df.columns)}")
            return df
        except Exception as e:
            logger.error(f"Error converting to DataFrame: {e}")
            raise

    @staticmethod
    def find_first_rarest_word(text: str) -> str:
        """Find the rarest word (first one) in text"""
        if not text or not isinstance(text, str):
            logger.debug("Empty or invalid text")
            return ""

        words = text.split()
        if not words:
            logger.debug("No words in text")
            return ""

        count = Counter(words)
        min_freq = min(count.values())

        for word in words:
            if count[word] == min_freq:
                logger.debug(f"Found rare word: '{word}' (frequency: {min_freq})")
                return word

        return ""

    @staticmethod
    def find_weapons(text: str, weapons: set) -> str:
        """Find first weapon in text from blacklist"""
        if not text or not isinstance(text, str):
            logger.debug("Empty or invalid text for weapon check")
            return ""

        if not weapons:
            logger.warning("Weapons list is empty")
            return ""
        weapons_lower = {w.lower() for w in weapons}
        words = text.split()
        for word in words:
            if word.lower() in weapons_lower:
                logger.debug(f"Weapon found: '{word}'")
                return word

        logger.debug("No weapons found in text")
        return ""

    @staticmethod
    def get_sentiment(text: str) -> str:
        """Get text sentiment: positive/negative/neutral"""
        if not text or not isinstance(text, str):
            logger.debug("Empty or invalid text for sentiment analysis")
            return "neutral"

        try:
            score = sid.polarity_scores(text)
            compound = score['compound']

            if compound >= 0.5:
                sentiment = "positive"
            elif compound <= -0.5:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            logger.debug(f"Text sentiment: {sentiment} (score: {compound:.3f})")
            return sentiment

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return "neutral"