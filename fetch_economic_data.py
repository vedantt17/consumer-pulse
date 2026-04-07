import pandas as pd
import requests
from datetime import datetime
import os
import io

def fetch_fred_series(series_id, start_date):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start_date}"
    response = requests.get(url)
    if response.status_code == 200:
        df = pd.read_csv(io.StringIO(response.text), index_col='observation_date', parse_dates=True)
        return df
    else:
        print(f"Failed to fetch {series_id}. Status code: {response.status_code}")
        return None

def fetch_fred_data():
    # Define the series to pull
    series_map = {
        'UMCSENT': 'Consumer Sentiment',
        'PCE': 'PCE Total',
        'PCEDG': 'PCE Durables',
        'PCEND': 'PCE Nondurables',
        'PCES': 'PCE Services',
        'DSPIC96': 'Real Disposable Income',
        'USREC': 'Recession Flag'
    }
    
    start_date = '2000-01-01'
    print(f"Fetching data from {start_date}...")
    
    try:
        data_frames = []
        for series_id, col_name in series_map.items():
            print(f"Pulling {series_id}...")
            df = fetch_fred_series(series_id, start_date)
            if df is not None:
                df.columns = [col_name]
                # Filter '.' or non-numeric values (FRED uses '.' for missing data)
                df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                data_frames.append(df)
            
        if not data_frames:
            return None

        # Merge all dataframes on the index (Date)
        master_df = data_frames[0]
        for df in data_frames[1:]:
            master_df = master_df.merge(df, left_index=True, right_index=True, how='outer')
            
        # Resample to monthly frequency (MS = Month Start)
        master_df = master_df.resample('MS').mean()
        
        # Handle missing values
        master_df = master_df.ffill().bfill()
        
        # Filter from January 2000 to present explicitly
        master_df = master_df[master_df.index >= '2000-01-01']
        
        # Ensure the Recession Flag is binary (0 or 1)
        master_df['Recession Flag'] = master_df['Recession Flag'].apply(lambda x: 1 if x >= 0.5 else 0)
        
        # Reset index and name the date column
        master_df.index.name = 'Date'
        master_df.reset_index(inplace=True)
        
        # Save to CSV
        output_path = 'consumer_sentiment_spending_data.csv'
        master_df.to_csv(output_path, index=False)
        print(f"Successfully saved clean dataset to {output_path}")
        
        return master_df

    except Exception as e:
        print(f"Error processing data: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    df = fetch_fred_data()
    if df is not None:
        print("\nFirst 5 rows of the dataset:")
        print(df.head())
        print("\nLast 5 rows of the dataset:")
        print(df.tail())
