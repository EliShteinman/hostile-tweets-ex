import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter
import re
import logging

logger = logging.getLogger(__name__)

# הורדת VADER lexicon
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')


class DataProcessor:
    """
    process the data
    """

    def __init__(self, weapons_file_path='data/weapons.txt'):
        self.sid = SentimentIntensityAnalyzer()
        self.weapons_list = self._load_weapons(weapons_file_path)

    def _load_weapons(self, file_path):
        """load the weapons list from a file"""
        try:
            with open(file_path, 'r') as f:
                # read the file line by line
                return {line.strip().lower() for line in f if line.strip()}
        except FileNotFoundError:
            logger.error(f"Weapons file not found: {file_path}")
            return set()

    def _find_rarest_word(self, df):
        """מוצא את המילה הנדירה ביותר עבור כל טקסט"""
        if df.empty:
            print("no data to process")
            return pd.Series()

        print("finding rarest word...")
        print(f"DataFrame columns: {df.columns.tolist()}")

        # בודק איזה שדה קיים - Text או original_text
        text_column = None
        if 'Text' in df.columns:
            text_column = 'Text'
        elif 'original_text' in df.columns:
            text_column = 'original_text'
        else:
            logger.error("No text column found!")
            return pd.Series([''] * len(df))

        print(f"Using text column: {text_column}")

        # בונה רשימת כל המילים
        all_words = ' '.join(df[text_column].dropna().astype(str)).lower().split()
        # ספירת תדירות כל מילה
        word_counts = Counter(all_words)

        def get_rarest_for_text(text):
            if not isinstance(text, str) or not text.strip():
                return ""

            words_in_text = list(set(text.lower().split()))
            rarest_word = None
            min_count = float('inf')

            for word in words_in_text:
                if word_counts[word] < min_count:
                    min_count = word_counts[word]
                    rarest_word = word
            return rarest_word if rarest_word else ""

        return df[text_column].apply(get_rarest_for_text)

    def _get_sentiment(self, text):
        """calculate the sentiment of the text"""
        if not isinstance(text, str) or not text.strip():
            return "neutral"

        try:
            score = self.sid.polarity_scores(text)['compound']

            if score >= 0.5:
                return "positive"
            elif score <= -0.5:
                return "negative"
            else:
                return "neutral"
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return "neutral"

    def _find_weapons(self, text):
        """find the first weapon in the text."""
        if not isinstance(text, str) or not text.strip():
            return ""

        try:
            text_lower = text.lower()

            for weapon in self.weapons_list:
                # use regex to check if the weapon is in the text
                if re.search(r'\b' + re.escape(weapon) + r'\b', text_lower):
                    return weapon
            return ""
        except Exception as e:
            logger.warning(f"Weapon detection failed: {e}")
            return ""

    def process_data(self, df):
        """
        the main function of the class. process the data and return a DataFrame.
        """
        if df.empty:
            return df

        processed_df = df.copy()

        # בודק איזה שדה טקסט קיים
        text_column = None
        if 'Text' in df.columns:
            text_column = 'Text'
        elif 'original_text' in df.columns:
            text_column = 'original_text'
        else:
            logger.error("No text column found in DataFrame!")
            return processed_df

        print(f"Processing with text column: {text_column}")

        # יוצר שדה original_text אם לא קיים (לתאימות)
        if 'original_text' not in processed_df.columns:
            processed_df['original_text'] = processed_df[text_column]

        # 1. finding the rarest word
        try:
            processed_df['rarest_word'] = self._find_rarest_word(processed_df)
        except Exception as e:
            logger.error(f"Error in rarest word processing: {e}")
            processed_df['rarest_word'] = ""

        # 2. finding the sentiment
        try:
            processed_df['sentiment'] = processed_df[text_column].apply(self._get_sentiment)
        except Exception as e:
            logger.error(f"Error in sentiment processing: {e}")
            processed_df['sentiment'] = "neutral"

        # 3. finding the weapons name
        try:
            processed_df['weapons_detected'] = processed_df[text_column].apply(self._find_weapons)
        except Exception as e:
            logger.error(f"Error in weapons processing: {e}")
            processed_df['weapons_detected'] = ""

        print(f"Processing completed. Final columns: {processed_df.columns.tolist()}")
        return processed_df