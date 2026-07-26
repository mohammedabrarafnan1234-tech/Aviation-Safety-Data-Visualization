import pandas as pd
import numpy as np
import requests
import io
import ssl
import os

# Bypass SSL certificate verification for macOS
ssl._create_default_https_context = ssl._create_unverified_context

def parse_coordinate(val):
    if pd.isna(val):
        return np.nan
    val_str = str(val).strip()
    if not val_str:
        return np.nan
    try:
        # Check if it is a simple float first
        return float(val_str)
    except ValueError:
        pass
    
    # Parse DMS or degrees with compass direction (e.g. 340512N, 1204512W, 34.08N)
    try:
        direction = val_str[-1].upper()
        if direction in ['N', 'S', 'E', 'W']:
            numeric_part = val_str[:-1].strip()
            if ' ' in numeric_part:
                parts = [p for p in numeric_part.split(' ') if p.strip()]
                deg = float(parts[0])
                min_val = float(parts[1]) if len(parts) > 1 else 0.0
                sec_val = float(parts[2]) if len(parts) > 2 else 0.0
                decimal = deg + min_val / 60.0 + sec_val / 3600.0
            else:
                if '.' in numeric_part:
                    decimal = float(numeric_part)
                else:
                    if len(numeric_part) >= 6:
                        deg = float(numeric_part[:-4])
                        min_val = float(numeric_part[-4:-2])
                        sec_val = float(numeric_part[-2:])
                        decimal = deg + min_val / 60.0 + sec_val / 3600.0
                    elif len(numeric_part) >= 4:
                        deg = float(numeric_part[:-2])
                        min_val = float(numeric_part[-2:])
                        decimal = deg + min_val / 60.0
                    else:
                        decimal = float(numeric_part)
            
            if direction in ['S', 'W']:
                decimal = -decimal
            return decimal
    except Exception:
        return np.nan
    return np.nan

def main():
    print("Starting Aviation Accidents data download and cleaning pipeline...")
    
    # 1. Define URLs
    url = 'https://raw.githubusercontent.com/ShreyaPatil1199/Aircraft_Damage_Prediction/master/AviationData.csv'
    
    os.makedirs("data", exist_ok=True)
    
    # 2. Download and read dataset
    print("Downloading dataset...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to download data: HTTP {response.status_code}")
        
    print("Reading CSV data...")
    try:
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')), low_memory=False)
    except Exception:
        df = pd.read_csv(io.StringIO(response.content.decode('latin-1')), low_memory=False)
        
    print(f"Loaded raw data: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # 3. Clean columns
    print("Cleaning columns...")
    
    # Standardize column names to snake_case
    df.columns = [col.replace('.', '_').replace(' ', '_').lower() for col in df.columns]
    
    # Parse event date and extract temporal attributes
    print("Parsing dates...")
    df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')
    df = df[df['event_date'].notna()]  # Drop rows with invalid dates
    df['year'] = df['event_date'].dt.year
    df['month'] = df['event_date'].dt.month
    df['day_of_week'] = df['event_date'].dt.day_name()
    
    # Filter years (let's keep 1982 to 2026, as 1982 is when modern NTSB logging began consistently)
    df = df[(df['year'] >= 1982) & (df['year'] <= 2026)]
    
    # Parse coordinates
    print("Parsing coordinates (Latitude & Longitude)...")
    df['latitude'] = df['latitude'].apply(parse_coordinate)
    df['longitude'] = df['longitude'].apply(parse_coordinate)
    
    # Standardize categorical columns
    print("Cleaning categories...")
    categorical_cols = [
        'investigation_type', 'aircraft_damage', 'aircraft_category', 
        'engine_type', 'weather_condition', 'broad_phase_of_flight', 
        'purpose_of_flight', 'make', 'model'
    ]
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
            df[col] = df[col].replace({'Nan': 'Unknown', 'N/A': 'Unknown', '': 'Unknown'})
            df[col] = df[col].fillna('Unknown')
            
    # Normalize Weather Condition to Vmc, Imc, or Unknown
    if 'weather_condition' in df.columns:
        df['weather_condition'] = df['weather_condition'].replace({
            'Vmc': 'VMC', 'Imc': 'IMC', 'Unk': 'Unknown', 'Unknown': 'Unknown'
        })
        
    # Clean up numerical columns
    print("Cleaning numerical columns...")
    numerical_cols = [
        'number_of_engines', 'total_fatal_injuries', 
        'total_serious_injuries', 'total_minor_injuries', 'total_uninjured'
    ]
    for col in numerical_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # Let's set default number of engines for non-zero cases
    df['number_of_engines'] = df['number_of_engines'].apply(lambda x: 1.0 if x <= 0 else x)
    
    # Compute total passengers on board
    df['total_on_board'] = (
        df['total_fatal_injuries'] + 
        df['total_serious_injuries'] + 
        df['total_minor_injuries'] + 
        df['total_uninjured']
    )
    
    # Calculate fatality rate
    df['fatality_rate'] = df.apply(
        lambda row: row['total_fatal_injuries'] / row['total_on_board'] if row['total_on_board'] > 0 else 0.0, 
        axis=1
    )
    
    # Parse Location to extract State/Country if US
    print("Cleaning locations...")
    def extract_state_country(row):
        loc = str(row['location']).strip()
        country = str(row['country']).strip()
        
        if ',' in loc:
            parts = loc.split(',')
            state = parts[-1].strip().upper()
            city = parts[0].strip()
            return city, state, country
        return loc, 'Unknown', country

    loc_parsed = df.apply(extract_state_country, axis=1, result_type='expand')
    df['city'] = loc_parsed[0]
    df['state_or_region'] = loc_parsed[1]
    
    # Clean Make column (e.g. Cessna, Boeing) to collapse minor spelling variations
    print("Standardizing manufacturers...")
    def standardize_make(make_val):
        make_str = str(make_val).upper().strip()
        if 'CESSNA' in make_str:
            return 'Cessna'
        elif 'BOEING' in make_str:
            return 'Boeing'
        elif 'PIPER' in make_str:
            return 'Piper'
        elif 'BEECH' in make_str:
            return 'Beechcraft'
        elif 'BELL' in make_str:
            return 'Bell'
        elif 'ROBINSON' in make_str:
            return 'Robinson'
        elif 'MOONEY' in make_str:
            return 'Mooney'
        elif 'GRUMMAN' in make_str:
            return 'Grumman'
        elif 'AIRBUS' in make_str:
            return 'Airbus'
        elif 'MCDONNELL' in make_str or 'DOUGLAS' in make_str:
            return 'McDonnell Douglas'
        elif 'SCHWEIZER' in make_str:
            return 'Schweizer'
        elif 'AERO' in make_str:
            return 'Aero Commander'
        elif 'CHAMPION' in make_str:
            return 'Champion'
        elif 'Unknown' in make_str or 'UNKNOWN' in make_str:
            return 'Unknown'
        return make_val
        
    df['make_cleaned'] = df['make'].apply(standardize_make)
    
    # 4. Save cleaned dataset
    output_path = "data/aviation_accidents_master.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved cleaned master dataset to: {output_path} ({df.shape[0]} rows)")
    
    print("\nData pipeline completed successfully!")

if __name__ == "__main__":
    main()
