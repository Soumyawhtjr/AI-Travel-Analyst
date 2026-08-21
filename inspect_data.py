
# Loading and Inspecting the flight price dataset.
import pandas as pd

# Path to the flight pricing dataset
DATA_PATH = "data/flight_pricing_dataset.csv"  

# Load the dataset into a DataFrame
df = pd.read_csv(DATA_PATH)

# Inspect the size of the dataset
print("=" * 60)
print("SHAPE (rows, columns):", df.shape)

# Inspect column names and data types
print("=" * 60)
print("COLUMN NAMES & DTYPES:")
print(df.dtypes)

# Preview the first five rows
print("=" * 60)
print("FIRST 5 ROWS:")
print(df.head())

# Check for missing values in each column
print("=" * 60)
print("MISSING VALUES PER COLUMN:")
print(df.isnull().sum())

# Check for duplicate rows
print("=" * 60)
print("DUPLICATE ROWS:", df.duplicated().sum())

# Generate basic descriptive statistics
print("=" * 60)
print("BASIC STATS (numeric columns):")
print(df.describe())

# Inspect categorical columns
print("=" * 60)
print("UNIQUE VALUES PER COLUMN (categorical-looking ones):")

for col in df.select_dtypes(include="object").columns:
    print(f"\n{col}: {df[col].nunique()} unique values")
    print(df[col].unique()[:10])  
