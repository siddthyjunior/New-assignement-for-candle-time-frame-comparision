import os
import boto3
import pandas as pd
from io import BytesIO

# --- CONFIGURATION ---
R2_ENDPOINT_URL = "https://cbabd13f6c54798a9ec05df5b8070a6e.r2.cloudflarestorage.com"
ACCESS_KEY = "5c8ea9c516abfc78987bc98c70d2868a"
SECRET_KEY = "0cf64f9f0b64f6008cf5efe1529c6772daa7d7d0822f5db42a7c6a1e41b3cadf"
BUCKET_NAME = "desiquant"
PREFIX = "data/candles/BANKNIFTY/2024-01-10/"
LOCAL_DOWNLOAD_DIR = "data_downloaded"
OUTPUT_DIR = "5min_candles"

# --- PART 1: DOWNLOAD DATA ---
def download_data():
    print("Step 1: Connecting to Cloud Storage...")
    s3_client = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    
    if not os.path.exists(LOCAL_DOWNLOAD_DIR):
        os.makedirs(LOCAL_DOWNLOAD_DIR)

    print(f"Listing files in {BUCKET_NAME}/{PREFIX}")
    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)
    
    downloaded_files = []
    
    if 'Contents' in response:
        for obj in response['Contents']:
            file_key = obj['Key']
            filename = os.path.basename(file_key)
            if not filename: continue
                
            local_path = os.path.join(LOCAL_DOWNLOAD_DIR, filename)
            
            if not os.path.exists(local_path):
                print(f"Downloading {filename}...")
                s3_client.download_file(BUCKET_NAME, file_key, local_path)
            else:
                print(f"File {filename} already exists. Skipping download.")
                
            downloaded_files.append(local_path)
    else:
        print("No files found!")
        
    return downloaded_files

# --- PART 2: PROCESS CANDLES ---
def process_file(filepath):
    print(f"Processing {filepath}...")
    try:
        df = pd.read_parquet(filepath, engine='pyarrow')
    except Exception as e:
        print(f"CRITICAL ERROR reading {filepath}: {e}")
        return None

    df.columns = [c.lower() for c in df.columns]
    
    time_col = None
    for col in df.columns:
        if 'time' in col or 'date' in col:
            time_col = col
            break
    if not time_col: time_col = df.columns[0] 

    df[time_col] = pd.to_datetime(df[time_col])
    target_date = "2024-01-10"
    df = df[df[time_col].dt.date == pd.to_datetime(target_date).date()]
    
    if df.empty:
        print(f"Skipping {filepath} (No data for {target_date})")
        return None

    df = df.set_index(time_col)
    
    agg_dict = {}
    if 'open' in df.columns: agg_dict['open'] = 'first'
    if 'high' in df.columns: agg_dict['high'] = 'max'
    if 'low' in df.columns: agg_dict['low'] = 'min'
    if 'close' in df.columns: agg_dict['close'] = 'last'
    
    if not agg_dict:
        print(f"Skipping {filepath} - could not find Open/High/Low/Close columns")
        return None

    df_5min = df.resample('5min').agg(agg_dict)
    df_5min = df_5min.dropna()
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    output_filename = os.path.basename(filepath).split('.')[0] + "_5min.csv"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    df_5min.to_csv(output_path)
    print(f"Saved: {output_path}")

    calculate_fibonacci_pivots(df, os.path.basename(filepath))
    
    # RETURN THE DATAFRAME FOR ANALYSIS
    return df_5min

# --- PART 3: BONUS (Fibonacci) ---
def calculate_fibonacci_pivots(daily_df, filename):
    if not {'high', 'low', 'close'}.issubset(daily_df.columns):
        return

    day_high = daily_df['high'].max()
    day_low = daily_df['low'].min()
    day_close = daily_df['close'].iloc[-1]
    
    P = (day_high + day_low + day_close) / 3
    diff = day_high - day_low
    
    print(f"\n--- FIBONACCI PIVOTS for {filename} ---")
    print(f"Pivot: {P:.2f}")
    print(f"R1: {P + 0.382 * diff:.2f} | S1: {P - 0.382 * diff:.2f}")
    print(f"R2: {P + 0.618 * diff:.2f} | S2: {P - 0.618 * diff:.2f}")
    print(f"R3: {P + diff:.2f}       | S3: {P - diff:.2f}")
    print("---------------------------------------\n")

# --- PART 4: ANALYSIS UTILS (For Interview Questions) ---

def get_candle_for_timestamp(df_5min, timestamp_str):
    """Finds a specific candle (e.g., 10:23 -> 10:20 bucket)"""
    print(f"\n--- LOOKUP: {timestamp_str} ---")
    lookup_time = pd.Timestamp(f"2024-01-10 {timestamp_str}:00")
    candle_time = lookup_time.floor('5min')
    
    try:
        row = df_5min.loc[candle_time]
        print(f"Mapped {timestamp_str} -> {candle_time.strftime('%H:%M')}")
        print(row)
        return row
    except KeyError:
        print(f"No data found for {candle_time}")
        return None

def compare_candles(df_5min, time1_str, time2_str):
    """Compares two candles side-by-side"""
    print(f"\n--- COMPARING {time1_str} vs {time2_str} ---")
    t1 = pd.Timestamp(f"2024-01-10 {time1_str}:00").floor('5min')
    t2 = pd.Timestamp(f"2024-01-10 {time2_str}:00").floor('5min')
    
    try:
        c1 = df_5min.loc[t1]
        c2 = df_5min.loc[t2]
        
        diff = c2['close'] - c1['close']
        pct_change = (diff / c1['close']) * 100
        
        print(f"{'Metric':<10} | {t1.strftime('%H:%M'):<10} | {t2.strftime('%H:%M')}")
        print("-" * 45)
        print(f"{'Open':<10} | {c1['open']:<10} | {c2['open']}")
        print(f"{'High':<10} | {c1['high']:<10} | {c2['high']}")
        print(f"{'Low':<10} | {c1['low']:<10} | {c2['low']}")
        print(f"{'Close':<10} | {c1['close']:<10} | {c2['close']}")
        print("-" * 45)
        print(f"Change: {diff:.2f} ({pct_change:.2f}%)")
        
    except KeyError:
        print("Error: One of the timestamps was not found.")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    files = download_data()
    
    last_df = None
    for f in files:
        last_df = process_file(f)

    # --- DEMO FOR INTERVIEWER ---
    if last_df is not None:
        # Question 1: Check specific timestamp
        get_candle_for_timestamp(last_df, "10:23")
        
        # Question 2: Compare two times
        compare_candles(last_df, "10:20", "10:45")