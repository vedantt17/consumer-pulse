import pandas as pd
import requests
import io
import time

def fetch_fred_csv(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text), index_col='observation_date', parse_dates=True)
            return df
        else:
            print(f"Failed to fetch {series_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
        return None

def main():
    # Mapping of categories and quintiles to FRED IDs (CEX data)
    # Pattern: CXU[CATEGORY]LB010[QUINTILE]M
    # Quintiles: 1 (Lowest), 2, 3, 4, 5 (Highest)
    
    quintiles = {
        'Q1': '02', # Lowest 20%
        'Q2': '03',
        'Q3': '04',
        'Q4': '05',
        'Q5': '06'  # Highest 20%
    }
    
    categories = {
        'TOTAL': 'TOTALEXP',
        'FOOD': 'FOODTOTL', # Corrected from FOODTOTAL
        'HOUSING': 'HOUSING',
        'APPAREL': 'APPAREL',
        'TRANS': 'TRANS',
        'HEALTH': 'HEALTH'
    }
    
    all_ce_data = []
    
    print("Fetching CE data for categories and quintiles...")
    for cat_label, cat_id in categories.items():
        for q_label, q_id in quintiles.items():
            series_id = f"CXU{cat_id}LB01{q_id}M"
            print(f"Fetching {series_id} ({cat_label}_{q_label})...")
            df = fetch_fred_csv(series_id)
            if df is not None:
                df.columns = [f"{cat_label}_{q_label}"]
                all_ce_data.append(df)
            time.sleep(0.5) # Avoid rate limiting
            
    if not all_ce_data:
        print("No CE data fetched. Exiting.")
        return

    # Merge all CE data
    ce_master = all_ce_data[0]
    for df in all_ce_data[1:]:
        ce_master = ce_master.merge(df, left_index=True, right_index=True, how='outer')
    
    # CE data is annual. Create a 'Year' column for merging.
    ce_master['Year'] = ce_master.index.year
    
    # Normalize to monthly (divide by 12)
    val_cols = [c for c in ce_master.columns if c != 'Year']
    ce_master[val_cols] = ce_master[val_cols] / 12.0
    
    # Load enriched dataset
    enriched_df = pd.read_csv('enriched_sentiment_spending_data.csv', parse_dates=['Date'])
    enriched_df['Year'] = enriched_df['Date'].dt.year
    
    # Merge on Year
    final_df = enriched_df.merge(ce_master, on='Year', how='left')
    
    # Compute Ratios (Highest to Lowest)
    for cat in categories.keys():
        high_col = f"{cat}_Q5"
        low_col = f"{cat}_Q1"
        if high_col in final_df.columns and low_col in final_df.columns:
            final_df[f"{cat}_Ratio_Q5_Q1"] = final_df[high_col] / final_df[low_col]
            
    # Handle missing years by forward/backward fill (CEX usually lags)
    final_df = final_df.ffill().bfill()
    
    # Save to CSV
    output_file = 'segmented_sentiment_spending_data.csv'
    final_df.to_csv(output_file, index=False)
    print(f"Successfully created segmented dataset: {output_file}")
    
    # Preview
    print("\nSample columns in segmented dataset:")
    print(final_df.columns.tolist()[:20])

if __name__ == "__main__":
    main()
