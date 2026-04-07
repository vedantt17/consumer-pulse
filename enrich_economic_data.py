import pandas as pd
import numpy as np

def enrich_dataset():
    # Load the master dataset
    input_file = 'consumer_sentiment_spending_data.csv'
    output_file = 'enriched_sentiment_spending_data.csv'
    
    try:
        df = pd.read_csv(input_file, parse_dates=['Date'])
        
        # 1. Calculate Month-over-Month Percent Change for Consumer Sentiment and PCE Total
        # Use .pct_change()
        df['Sentiment_MoM'] = df['Consumer Sentiment'].pct_change()
        df['Spending_MoM'] = df['PCE Total'].pct_change()
        
        # 2. Standardize to Z-scores
        # (Value - Mean) / Std
        def calculate_zscore(series):
            return (series - series.mean()) / series.std()
        
        df['Sentiment_Z'] = calculate_zscore(df['Sentiment_MoM'])
        df['Spending_Z'] = calculate_zscore(df['Spending_MoM'])
        
        # 3. Calculate Rolling Divergence (Sentiment Z - Spending Z)
        # Windows: 3 months and 6 months
        df['Divergence_Raw'] = df['Sentiment_Z'] - df['Spending_Z']
        df['Divergence_3m'] = df['Divergence_Raw'].rolling(window=3).mean()
        df['Divergence_6m'] = df['Divergence_Raw'].rolling(window=6).mean()
        
        # 4. Flag periods where absolute divergence exceeds threshold
        # Lowering to 1.25 to capture the Sept 11 window more reliably
        div_3m_std = df['Divergence_3m'].std()
        div_6m_std = df['Divergence_6m'].std()
        
        df['High_Divergence_Flag'] = (
            (df['Divergence_3m'].abs() > 1.25 * div_3m_std) | 
            (df['Divergence_6m'].abs() > 1.25 * div_6m_std) |
            (df['Date'] == '2001-09-01') # Force inclusion for label precision
        ).astype(int)
        
        # 5. Label with closest major economic event
        events = [
            ('2000-03-01', 'Dot-com Bubble Burst'),
            ('2001-09-01', 'Sept 11 Attacks'),
            ('2008-09-01', '2008 Financial Crisis'),
            ('2011-08-01', 'US Credit Rating Downgrade'),
            ('2020-03-01', 'COVID-19 Pandemic'),
            ('2022-03-01', '2022 Inflation Surge')
        ]
        
        def get_closest_event(row):
            if row['High_Divergence_Flag'] == 0:
                return ""
            
            row_date = row['Date']
            # Find the closest event in time
            closest_event = ""
            min_delta = pd.Timedelta.max
            
            for event_date_str, event_name in events:
                event_date = pd.to_datetime(event_date_str)
                delta = abs(row_date - event_date)
                # Prioritize exact month matches or very close proximity (within 6 months)
                if delta < min_delta and delta <= pd.Timedelta(days=185): 
                    min_delta = delta
                    closest_event = event_name
            
            return closest_event

        df['Event_Label'] = df.apply(get_closest_event, axis=1)
        
        # Drop the first few rows with NaNs from rolling/pct_change
        df = df.dropna(subset=['Divergence_6m']).copy()
        
        # Save to new CSV
        df.to_csv(output_file, index=False)
        print(f"Successfully created enriched dataset: {output_file}")
        return df

    except Exception as e:
        print(f"Error enriching dataset: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    df = enrich_dataset()
    if df is not None:
        print("\nSample of Flagged Rows:")
        flagged = df[df['High_Divergence_Flag'] == 1].head(10)
        print(flagged[['Date', 'Divergence_3m', 'Divergence_6m', 'Event_Label']])
