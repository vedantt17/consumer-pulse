# Consumer Pulse

![Python](https://img.shields.io/badge/python-3.8+-blue) ![License](https://img.shields.io/badge/license-MIT-green)

Consumer Pulse is a data pipeline and interactive dashboard that tracks how American consumer sentiment holds up against actual spending behavior. The core question it tries to answer is simple: when people say they feel good or bad about the economy, does their spending actually follow? And when it doesn't, what's going on?

The project pulls real economic data from FRED (Federal Reserve Economic Data), runs it through a series of enrichment and segmentation steps, and produces a self-contained HTML dashboard you can open in any browser, no server needed.

---

## What It Does

The pipeline runs in four stages, each handled by its own script:

**1. Fetch** (`fetch_economic_data.py`)

Pulls seven time series from FRED going back to January 2000:

- University of Michigan Consumer Sentiment Index
- Personal Consumption Expenditures (PCE) total and broken into durables, nondurables, and services
- Real Disposable Personal Income
- NBER Recession Flag

All series are resampled to monthly frequency and merged into a single CSV.

**2. Enrich** (`enrich_economic_data.py`)

Takes the raw data and adds analytical columns:

- Month-over-month percent change for sentiment and total spending
- Z-scores for both, so they're on the same scale
- A "divergence" signal (sentiment Z minus spending Z) smoothed over 3-month and 6-month rolling windows
- A flag for periods where the divergence exceeds 1.25 standard deviations
- Labels for the closest major economic event within 6 months of each flagged period (Dot-com bubble, Sept 11, 2008 Financial Crisis, COVID-19, 2022 Inflation Surge)

**3. Segment** (`segment_spending_data.py`)

Pulls Consumer Expenditure Survey (CEX) data from FRED, broken down by income quintile (lowest 20% through highest 20%) across six spending categories: food, housing, apparel, transportation, healthcare, and total. It merges this with the enriched dataset and computes Q5/Q1 spending ratios to show how unequal spending is across income groups.

**4. Dashboard** (`create_dashboard_final.py`)

Generates a dark-themed, fully interactive HTML dashboard with three pages:

- **Macro Overview** -- Consumer sentiment vs. PCE on a dual-axis chart with recession shading and event annotations. Three KPI cards show current sentiment, current 6-month divergence, and the peak divergence over the past 12 months (color-coded green/amber/red).
- **Category Breakdown** -- Z-score oscillations for durables, nondurables, and services compared against the sentiment baseline, making it easy to see which spending categories lead or lag sentiment shifts.
- **Income Segmentation** -- Monthly spending for the top and bottom income quintiles, plus a bar chart showing the Q5/Q1 ratio across all six spending categories.

---

## Files

| File | Description |
|---|---|
| `fetch_economic_data.py` | Pulls and cleans raw FRED data |
| `enrich_economic_data.py` | Adds divergence signals and event labels |
| `segment_spending_data.py` | Adds income quintile spending breakdown |
| `create_dashboard_final.py` | Builds the final HTML dashboard |
| `consumer_sentiment_spending_data.csv` | Raw output from the fetch step |
| `enriched_sentiment_spending_data.csv` | Output after enrichment |
| `segmented_sentiment_spending_data.csv` | Final dataset used by the dashboard |
| `sentiment_spending_dashboard_final.html` | The finished dashboard, open this in a browser |

---

## How to Run It

If you want to regenerate everything from scratch, run the scripts in order:

```bash
python fetch_economic_data.py
python enrich_economic_data.py
python segment_spending_data.py
python create_dashboard_final.py
```

Or just open `sentiment_spending_dashboard_final.html` directly in your browser if you want to skip the data refresh and use the CSVs already in the repo.

### Dependencies

```bash
pip install pandas numpy requests plotly
```

No API key is needed. All data is pulled from FRED's public CSV endpoint.

---

## Data Sources

- [FRED (Federal Reserve Bank of St. Louis)](https://fred.stlouisfed.org/) -- macroeconomic series including PCE, sentiment, disposable income, and recession flags
- [BLS Consumer Expenditure Survey via FRED](https://fred.stlouisfed.org/) -- income quintile spending data
- University of Michigan Surveys of Consumers -- the sentiment index (distributed through FRED as UMCSENT)
