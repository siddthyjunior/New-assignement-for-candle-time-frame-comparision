# BankNifty Options Data Pipeline

## Overview
This project is an automated data engineering pipeline designed to ingest, process, and analyze high-frequency BankNifty options data. It replaces manual data retrieval with a robust Python script that fetches raw Parquet files from Cloudflare R2, resamples them into standard OHLC candles, and performs technical analysis.

## Key Features
* **Automated Ingestion:** Uses `boto3` to programmatically fetch data from R2/S3, eliminating the need for manual CLI tools (`s3cmd`).
* **Parquet Processing:** Implements a robust reader using the `pyarrow` engine to correctly handle binary `.parquet.gz` files that standard Pandas readers often misinterpret.
* **Time-Series Resampling:** Converts 1-minute high-frequency data into 5-minute OHLC (Open-High-Low-Close) candles.
* **Technical Analysis:**
    * Calculates **Fibonacci Pivot Points** (Pivot, R1-R3, S1-S3) for identifying daily support and resistance levels.
    * Includes a **Comparison Utility** to analyze price trends between specific time buckets (e.g., 10:20 vs 10:45).
    * Includes a **Timestamp Lookup** tool to instantly retrieve candle data for any specific time.

## Tech Stack
* **Python 3.10+**
* **Pandas:** For efficient time-series manipulation and resampling.
* **Boto3:** For AWS S3 / Cloudflare R2 connectivity.
* **PyArrow:** For efficient binary file parsing.

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/](https://github.com/)[YOUR_USERNAME]/quant-intern-assignment.git
    cd quant-intern-assignment
    ```

2.  **Install dependencies:**
    ```bash
    pip install pandas boto3 pyarrow fastparquet
    ```

3.  **Run the pipeline:**
    ```bash
    python main.py
    ```

## Project Structure
* `main.py`: The core script handling download, processing, and analysis.
* `data_downloaded/`: Directory where raw Parquet files are stored (auto-created).
* `5min_candles/`: Directory where processed 5-minute CSVs are saved (auto-created).

## Logic & Design Decisions

### 1. Data Ingestion
Instead of using external CLI tools like `s3cmd`, I implemented a native Python `boto3` client. This makes the pipeline self-contained, OS-agnostic, and easier to schedule in a production environment (e.g., via Airflow or Cron).

### 2. Handling Parquet Format
The raw data files (`.parquet.gz`) contained a Parquet binary header (`PA...`). Standard `pd.read_csv` or `pd.read_parquet` (without engine specification) often fails on compressed archives. I explicitly defined `engine='pyarrow'` to ensure accurate parsing of the binary columnar format.

### 3. Resampling Logic
To convert 1-minute data to 5-minute candles, I used time-series resampling with the following aggregation rules:
* **Open:** First price of the interval.
* **High:** Maximum price of the interval.
* **Low:** Minimum price of the interval.
* **Close:** Last price of the interval.

*Note: I used "Left Labeling" for time buckets (e.g., 10:23 falls into the 10:20 bucket).*

### 4. Mathematical Edge Cases
For the Fibonacci Pivot calculation on high-volatility Out-of-the-Money options, the Support levels (S1, S2, S3) may mathematically result in negative values if the daily range ($High - Low$) exceeds the price itself. In this implementation, I output the raw mathematical result to remain true to the formula, though a production trading system would floor these values at 0.

## Usage Example (Analysis Tools)
The script includes utility functions for quick analysis.

**Lookup a specific timestamp:**
```python
# Finds the 5-min bucket for 10:23
get_candle_for_timestamp(df, "10:23")

# Shows price change between 10:20 and 10:45
compare_candles(df, "10:20", "10:45")

### **Why this README works:**
1.  **"Logic & Design Decisions" Section:** This is the most important part. It answers the interview questions *before* they even ask them. It shows you aren't just a coder, but an **Engineer** who makes decisions.
2.  **Professional Formatting:** It uses code blocks, bold text, and clear headers.
3.  **Honesty:** It explicitly mentions the "Negative Support Levels" issue under "Mathematical Edge Cases." This proves you understand the data.
