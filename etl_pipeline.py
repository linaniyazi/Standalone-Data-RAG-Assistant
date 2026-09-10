import pandas as pd
import logging
import os
from cleaning_functions import clean_dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("etl_pipeline.log",encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract(source_path):
    """Read raw data from a CSV file."""
    if not os.path.exists(source_path):
        logger.error(f"Source file not found: {source_path}")
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    df = pd.read_csv(source_path)
    logger.info(f"Extracted {len(df)} rows from {source_path}")
    return df

def transform(df):
    """Clean the raw data using existing cleaning functions."""
    rows_before = len(df)
    df_clean = clean_dataset(df)
    rows_after = len(df_clean)
    logger.info(f"Transformed data: {rows_before} → {rows_after} rows")
    return df_clean

def load(df, output_path):
    """Save the cleaned data to a CSV file."""
    df.to_csv(output_path, index=False)
    logger.info(f"Loaded {len(df)} rows to {output_path}")
    
def run_pipeline(source_path, output_path):
    """Run the full ETL pipeline: Extract, Transform, Load."""
    logger.info("Pipeline started")
    try:
        df_raw = extract(source_path)
        df_clean = transform(df_raw)
        load(df_clean, output_path)
        logger.info("Pipeline finished successfully")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    
if __name__ == "__main__":
    run_pipeline(
        source_path="data/retail_store_sales.csv",
        output_path="data/retail_store_sales_cleaned.csv"
    )