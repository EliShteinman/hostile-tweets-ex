from .processor import DataProcessor
import pandas as pd
import logging

logger = logging.getLogger(__name__)
class AnalysisManager:
    def __init__(self, df: pd.DataFrame):
        self.raw_data_df = df
        self.processor = DataProcessor()
        self.processed_data = None
        self._processing_completed = False  # ← דגל למניעת עיבוד כפול

    def debug_data_schema(self):
        """פונקציה לדיבוג סכמת הנתונים"""
        print(f"DataFrame shape: {self.raw_data_df.shape}")
        print(f"DataFrame columns: {list(self.raw_data_df.columns)}")
        if not self.raw_data_df.empty:
            print(f"Sample record:")
            sample = self.raw_data_df.iloc[0].to_dict()
            print(sample)
        return self.raw_data_df.columns.tolist()

    def run_full_analysis(self):
        """מריץ את כל תהליך הניתוח - רק פעם אחת!"""

        # אם כבר עיבדנו - לא נעשה זאת שוב
        if self._processing_completed:
            logger.info("Analysis already completed - skipping")
            return

        try:
            if self.raw_data_df.empty:
                logger.warning("Empty DataFrame - setting empty results")
                self.processed_data = []
                self._processing_completed = True
                return

            logger.info("🔄 Starting data processing...")

            # דיבוג סכמה
            columns = self.debug_data_schema()
            logger.info(f"Available columns: {columns}")

            # עיבוד הנתונים
            processed_df = self.processor.process_data(self.raw_data_df)

            if processed_df.empty:
                logger.warning("Processing returned empty DataFrame")
                self.processed_data = []
                self._processing_completed = True
                return

            # המרה לפורמט הנדרש
            logger.info("Converting to output format...")
            result = []

            for index, row in processed_df.iterrows():
                try:
                    # בודק איזה שדה טקסט קיים
                    original_text = ""
                    if 'original_text' in row:
                        original_text = str(row['original_text'])
                    elif 'Text' in row:
                        original_text = str(row['Text'])

                    record = {
                        "id": str(row.get('_id', f"row_{index}")),
                        "original_text": original_text,
                        "rarest_word": str(row.get('rarest_word', '')),
                        "sentiment": str(row.get('sentiment', 'neutral')),
                        "weapons_detected": str(row.get('weapons_detected', ''))
                    }
                    result.append(record)

                except Exception as e:
                    logger.error(f"Error processing row {index}: {e}")
                    # הוסף רשומה ריקה במקרה של שגיאה
                    record = {
                        "id": str(index),
                        "original_text": "",
                        "rarest_word": "",
                        "sentiment": "neutral",
                        "weapons_detected": ""
                    }
                    result.append(record)

            self.processed_data = result
            self._processing_completed = True  # ← סמן שסיימנו
            logger.info(f"Analysis completed successfully - {len(result)} records processed")

        except Exception as e:
            logger.error(f"Fatal error in analysis: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # הגדר תוצאה ריקה במקרה של שגיאה
            self.processed_data = []
            self._processing_completed = True

    def get_processed_data(self):
        """מחזיר את הנתונים המעובדים - ללא עיבוד נוסף!"""

        # אם עוד לא עיבדנו - תריץ עיבוד
        if not self._processing_completed:
            logger.info("Data not processed yet - running analysis")
            self.run_full_analysis()

        return self.processed_data if self.processed_data is not None else []