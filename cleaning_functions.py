import pandas as pd
import numpy as np


def fill_missing_totals(df):
    """
    Fill missing values in Price Per Unit, Quantity, or Total Spent
    using the relationship: Total Spent = Price Per Unit * Quantity
    """
    df = df.copy()
    
    # Case 1: Total Spent missing, Price and Quantity present
    mask = df['Total Spent'].isnull() & df['Price Per Unit'].notnull() & df['Quantity'].notnull()
    df.loc[mask, 'Total Spent'] = df.loc[mask, 'Price Per Unit'] * df.loc[mask, 'Quantity']
    
    # Case 2: Price Per Unit missing, Total Spent and Quantity present
    mask = df['Price Per Unit'].isnull() & df['Total Spent'].notnull() & df['Quantity'].notnull()
    df.loc[mask, 'Price Per Unit'] = df.loc[mask, 'Total Spent'] / df.loc[mask, 'Quantity']
    
    # Case 3: Quantity missing, Total Spent and Price Per Unit present
    mask = df['Quantity'].isnull() & df['Total Spent'].notnull() & df['Price Per Unit'].notnull()
    df.loc[mask, 'Quantity'] = df.loc[mask, 'Total Spent'] / df.loc[mask, 'Price Per Unit']
    
    return df

def fill_missing_discount(df):
    """Treat missing Discount Applied as False (no discount recorded)."""
    df = df.copy()
    df['Discount Applied'] = df['Discount Applied'].fillna(False)
    return df

def convert_date_column(df, column='Transaction Date'):
    """Convert a date column from string to datetime."""
    df = df.copy()
    df[column] = pd.to_datetime(df[column], errors='coerce')
    return df

def handle_remaining_missing(df):
    """Drop rows that still have missing critical values after other fixes."""
    df = df.copy()
    before = len(df)
    df = df.dropna(subset=['Price Per Unit', 'Quantity', 'Total Spent'])
    after = len(df)
    print(f"Dropped {before - after} rows with unrecoverable missing values.")
    return df


def fill_missing_item(df):
    """Fill missing Item values with 'Unknown'."""
    df = df.copy()
    df['Item'] = df['Item'].fillna('Unknown')
    return df


def clean_dataset(df):
    """Run the full cleaning pipeline on the raw dataframe."""
    df = fill_missing_totals(df)
    df = fill_missing_discount(df)
    df = fill_missing_item(df)
    df = convert_date_column(df)
    df = handle_remaining_missing(df)
    return df