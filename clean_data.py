
import re
import pandas as pd
import numpy as np
import os

RAW_PATH = "data/flight_pricing_dataset.csv"
CLEAN_PATH = "data/flight_price_clean.csv"

# Standardizing airport codes and airport labels to city names.

LOCATION_MAP = {
    "HYD": "Hyderabad", "BOM": "Mumbai", "PNQ": "Pune", "DXB": "Dubai",
    "DEL": "Delhi", "BLR": "Bangalore", "MAA": "Chennai", "CCU": "Kolkata",
    "GOI": "Goa", "SIN": "Singapore",
    "Bangalore Airport": "Bangalore", "Jaipur Airport": "Jaipur",
    "Singapore Airport": "Singapore", "Hyderabad Airport": "Hyderabad",
    "Mumbai Airport": "Mumbai",
    "AMD": "Ahmedabad", "Ahmedabad Airport": "Ahmedabad",
    "BKK": "Bangkok", "Bangkok Airport": "Bangkok",
    "Chennai Airport": "Chennai",
    "DOH": "Doha", "Doha Airport": "Doha",
    "Delhi Airport": "Delhi",
    "Dubai Airport": "Dubai",
    "FRA": "Frankfurt", "Frankfurt Airport": "Frankfurt",
    "Goa Airport": "Goa",
    "JAI": "Jaipur",
    "JFK": "New York", "New York Airport": "New York",
    "Kolkata Airport": "Kolkata",
    "LHR": "London", "London Airport": "London",
    "Pune Airport": "Pune",
    "SYD": "Sydney", "Sydney Airport": "Sydney",
}

# Standardize the different representations of the number of stops.
STOPS_MAP = {
    "0": 0, "non-stop": 0,
    "1": 1, "1 stop": 1,
    "2": 2, "2 stops": 2,
}

# Convert passenger counts written as words into numbers.
PASSENGER_WORD_MAP = {
    "one": "1", "two": "2", "three": "3",
    "four": "4", "five": "5", "six": "6",
}


def parse_duration_to_minutes(value):
    """Convert duration values to minutes."""

    if pd.isna(value):
        return np.nan
    
    value = str(value).strip()

    match = re.match(r"(?:(\d+)h)?\s*(?:(\d+)m)?", value)
    if match and (match.group(1) or match.group(2)):
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        return hours * 60 + minutes
    try:
        return float(value) * 60  # decimal hours -> minutes
    except ValueError:
        return np.nan


def parse_time_to_hour(value):
    if pd.isna(value):
        return np.nan
    value = str(value).strip()
    try:
        if "AM" in value.upper() or "PM" in value.upper():
            return pd.to_datetime(value, format="%I:%M %p").hour
        return pd.to_datetime(value, format="%H:%M").hour
    except Exception:
        return np.nan


def hour_to_bucket(hour):
    if pd.isna(hour):
        return "Unknown"
    hour = int(hour)
    if 5 <= hour < 12:
        return "Morning"
    if 12 <= hour < 17:
        return "Afternoon"
    if 17 <= hour < 21:
        return "Evening"
    return "Night"


def report_unmapped_locations(df):
    """Flags Source/Destination values our mapping doesn't cover"""
    known_cities = set(LOCATION_MAP.values())
    for col in ["Source", "Destination"]:
        vals = df[col].dropna().unique()
        unmapped = [v for v in vals if v not in LOCATION_MAP and v not in known_cities]
        if unmapped:
            print(f"WARNING: {col} has unmapped values, add to LOCATION_MAP: {sorted(unmapped)}")


def load_and_clean(path=RAW_PATH):
    df = pd.read_csv(path)
    n_start = len(df)

    # 1. Drop exact duplicate rows
    df = df.drop_duplicates()
    n_after_dedup = len(df)

    text_cols_to_normalize = ["Airline", "Travel_Class", "Booking_Channel",
                               "Weekday", "Season", "Aircraft_Type"]
    for col in text_cols_to_normalize:
        df[col] = df[col].apply(lambda x: str(x).strip().title() if pd.notna(x) else x)

    # 2. Removing rows without Price
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df = df.dropna(subset=["Price"])

    ''' Capping unrealistic price outliers — a small number of prices reach 10L+, 
        which isn't realistic for any real flight and wasstretching every plot's axis. 
        Keep up to the 99th percentile.'''
    
    price_cap = df["Price"].quantile(0.99)
    n_before_cap = len(df)
    df = df[df["Price"] <= price_cap]
    print(f"Dropped {n_before_cap - len(df)} rows as price outliers "
          f"(above Rs {price_cap:,.0f})")

    # 3. Convert numeric columns from strings to numeric values.
    df["Distance_km"] = pd.to_numeric(df["Distance_km"], errors="coerce")
    df["Days_Before_Departure"] = pd.to_numeric(df["Days_Before_Departure"], errors="coerce")

    # 4. Passenger_Count: mix of digits and spelled-out numbers
    df["Passenger_Count"] = (
        df["Passenger_Count"].astype(str).str.lower().str.strip()
        .replace(PASSENGER_WORD_MAP)
    )
    df["Passenger_Count"] = pd.to_numeric(df["Passenger_Count"], errors="coerce")

    # 5. Standardize the different representations of the number of stops
    # and fill missing values with the most common value.
    df["Total_Stops"] = df["Total_Stops"].astype(str).str.strip().map(STOPS_MAP)
    df["Total_Stops"] = df["Total_Stops"].fillna(df["Total_Stops"].mode()[0])

    # 6. Source / Destination: standardize codes/labels to plain city names
    report_unmapped_locations(df)
    df["Source"] = df["Source"].replace(LOCATION_MAP)
    df["Destination"] = df["Destination"].replace(LOCATION_MAP)

    # 7. Duration -> minutes (one consistent numeric feature)
    df["Duration_Minutes"] = df["Duration"].apply(parse_duration_to_minutes)

    # 8. Departure/Arrival time -> hour + time-of-day bucket
    df["Departure_Hour"] = df["Departure_Time"].apply(parse_time_to_hour)
    df["Arrival_Hour"] = df["Arrival_Time"].apply(parse_time_to_hour)
    df["Departure_Period"] = df["Departure_Hour"].apply(hour_to_bucket)

    # 9. Convert departure dates to datetime and extract the month.
    df["Departure_Date"] = pd.to_datetime(df["Departure_Date"], errors="coerce")
    df["Departure_Month"] = df["Departure_Date"].dt.month_name()

    # 10. Remaining categorical missing values -> explicit "Unknown"
    
    categorical_cols = [
        "Airline", "Source", "Destination", "Travel_Class",
        "Season", "Weekday", "Aircraft_Type", "Booking_Channel",
    ]
    for col in categorical_cols:
        df[col] = df[col].fillna("Unknown")

    # 11. Remove rows missing important numeric values.
    df = df.dropna(subset=["Distance_km", "Days_Before_Departure", "Passenger_Count"])

    # 12. Final type cleanup
    df["Total_Stops"] = df["Total_Stops"].astype(int)
    df["Passenger_Count"] = df["Passenger_Count"].astype(int)
    df["Days_Before_Departure"] = df["Days_Before_Departure"].astype(int)

    n_final = len(df)
    print(f"Rows: {n_start} -> {n_after_dedup} after dedup -> {n_final} after cleaning")
    print(f"Dropped {n_start - n_final} rows total ({(n_start - n_final)/n_start:.1%})")

    return df


if __name__ == "__main__":
    df = load_and_clean()
    df.to_csv(CLEAN_PATH, index=False)
    print(f"\nSaved cleaned dataset to {CLEAN_PATH}")
    print("Exact location:", os.path.abspath(CLEAN_PATH))
    print(df.dtypes)
    print(df.head())
