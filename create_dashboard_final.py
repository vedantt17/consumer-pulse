import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import numpy as np

# Load the segmented dataset
df = pd.read_csv('segmented_sentiment_spending_data.csv', parse_dates=['Date'])

# Configuration & Constants
THEME_BG = "#0d1117"
THEME_CARD = "#161b22"
THEME_TEXT = "#c9d1d9"
THEME_PRIMARY = "#58a6ff"  # Electric Blue
THEME_SECONDARY = "#3fb950" # Emerald Green
THEME_ACCENT = "#d2a8ff"    # Purple
THEME_GRAY = "#30363d"

def get_color(val):
    abs_val = abs(val)
    if abs_val < 0.5: return "#3fb950" # Green
    if abs_val < 1.0: return "#d29922" # Amber
    return "#f85149" # Red

# Metrics
current_sentiment = df['Consumer Sentiment'].iloc[-1]
current_div = df['Divergence_6m'].iloc[-1]
latest_date = df['Date'].max()
one_year_ago = latest_date - pd.DateOffset(months=12)
peak_12m_div = df[df['Date'] >= one_year_ago]['Divergence_6m'].abs().max()

# 1. Page 1: Macro Overview
fig1 = make_subplots(specs=[[{"secondary_y": True}]])
fig1.add_trace(go.Scatter(x=df['Date'], y=df['Consumer Sentiment'], name="Sentiment", line=dict(color=THEME_PRIMARY, width=3)), secondary_y=False)
fig1.add_trace(go.Scatter(x=df['Date'], y=df['PCE Total'], name="PCE Total", line=dict(color=THEME_SECONDARY, width=3)), secondary_y=True)

recession_starts = df[df['Recession Flag'].diff() == 1]['Date']
recession_ends = df[df['Recession Flag'].diff() == -1]['Date']
for start, end in zip(recession_starts, recession_ends):
    fig1.add_vrect(x0=start, x1=end, fillcolor="#21262d", opacity=0.4, layer="below", line_width=0)

events = [
    {'date': '2008-09-01', 'text': '2008 Crisis'},
    {'date': '2020-03-01', 'text': 'COVID-19'},
    {'date': '2022-03-01', 'text': 'Inflation Surge'},
    {'date': '2025-01-01', 'text': 'Tariff Uncertainty'}
]
for event in events:
    valid_data = df[df['Date'] == event['date']]
    if not valid_data.empty:
        fig1.add_annotation(
            x=event['date'], y=valid_data['Consumer Sentiment'].values[0],
            text=event['text'], showarrow=False, bgcolor=THEME_GRAY, bordercolor=THEME_TEXT,
            font=dict(color=THEME_TEXT, size=10), borderpad=4, opacity=0.8, yshift=20, secondary_y=False
        )

fig1.update_layout(
    template="plotly_dark", paper_bgcolor=THEME_CARD, plot_bgcolor=THEME_CARD,
    margin=dict(l=40, r=40, t=20, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", title="Sentiment Index", range=[40, 120]),
    yaxis2=dict(gridcolor="#21262d", title="PCE (Billions $)", range=[5000, 22000])
)

# 2. Page 2: Category Breakdown
def calculate_z(series):
    mom = series.pct_change()
    return (mom - mom.mean()) / mom.std()

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df['Date'].values, y=df['Sentiment_Z'].values, name="Sentiment (Z)", line=dict(color=THEME_TEXT, dash='dot', width=1.5)))
fig2.add_trace(go.Scatter(x=df['Date'].values, y=calculate_z(df['PCE Durables']).values, name="Durables (Z)", line=dict(color="#f0883e", width=2)))
fig2.add_trace(go.Scatter(x=df['Date'].values, y=calculate_z(df['PCE Nondurables']).values, name="Nondurables (Z)", line=dict(color="#db61a2", width=2)))
fig2.add_trace(go.Scatter(x=df['Date'].values, y=calculate_z(df['PCE Services']).values, name="Services (Z)", line=dict(color="#3fb950", width=2)))

fig2.update_layout(
    template="plotly_dark", paper_bgcolor=THEME_CARD, plot_bgcolor=THEME_CARD,
    margin=dict(l=40, r=40, t=20, b=40), legend=dict(orientation="h"),
    hovermode="x unified", xaxis=dict(gridcolor="#21262d"), 
    yaxis=dict(gridcolor="#21262d", title="Std Devs (Z)", range=[-4, 4])
)

# 3. Page 3: Income Segmentation
fig3_area = go.Figure()
fig3_area.add_trace(go.Scatter(x=df['Date'].values, y=df['TOTAL_Q5'].values, name="Highest 20% (Q5)", line=dict(color="#58a6ff"), fill='tozeroy', fillcolor="rgba(88, 166, 255, 0.3)"))
fig3_area.add_trace(go.Scatter(x=df['Date'].values, y=df['TOTAL_Q1'].values, name="Lowest 20% (Q1)", line=dict(color="#f85149"), fill='tozeroy', fillcolor="rgba(248, 81, 73, 0.2)"))

fig3_area.update_layout(
    template="plotly_dark", paper_bgcolor=THEME_CARD, plot_bgcolor=THEME_CARD, 
    height=400, margin=dict(l=40, r=40, t=20, b=40), 
    yaxis=dict(title="Monthly Spending ($)", range=[0, 14000]),
    hovermode="x unified"
)

# FINAL FIX: Bar Chart with Category Isolation
cats = ['Food', 'Housing', 'Apparel', 'Transport', 'Healthcare', 'Total']
vals = [
    float(df['FOOD_Ratio_Q5_Q1'].iloc[-1]), 
    float(df['HOUSING_Ratio_Q5_Q1'].iloc[-1]), 
    float(df['APPAREL_Ratio_Q5_Q1'].iloc[-1]), 
    float(df['TRANS_Ratio_Q5_Q1'].iloc[-1]), 
    float(df['HEALTH_Ratio_Q5_Q1'].iloc[-1]), 
    float(df['TOTAL_Ratio_Q5_Q1'].iloc[-1])
]

# We use go.Bar with categorical x and ensure no date arrays are present in this scope
fig3_bar = go.Figure()
fig3_bar.add_trace(go.Bar(
    x=cats,
    y=vals,
    marker=dict(color=vals, colorscale=[[0, '#58a6ff'], [1, '#f0883e']]),
    text=[f"{r:.2f}x" for r in vals],
    textposition='auto',
))

# Force categorical axis and remove any potential date parsing
fig3_bar.update_xaxes(type='category', categoryorder='array', categoryarray=cats, gridcolor="#21262d")
fig3_bar.update_yaxes(title="Ratio (Q5/Q1)", gridcolor="#21262d")
fig3_bar.update_layout(
    template="plotly_dark", 
    paper_bgcolor=THEME_CARD, 
    plot_bgcolor=THEME_CARD, 
    height=350, 
    margin=dict(l=40, r=40, t=20, b=40),
    showlegend=False
)

# HTML Assembly
timestamp = datetime.now().strftime("%B %d, %Y")
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentiment & Spending Intel Final</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root {{ --bg: {THEME_BG}; --card: {THEME_CARD}; --text: {THEME_TEXT}; --primary: {THEME_PRIMARY}; --gray: {THEME_GRAY}; }}
        body {{ background-color: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; padding: 0; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid var(--gray); padding-bottom: 1rem; }}
        header h1 {{ font-size: 1.5rem; font-weight: 700; margin: 0; color: #fff; }}
        .nav-container {{ display: flex; justify-content: center; margin-bottom: 2.5rem; }}
        .pill-nav {{ background: var(--card); padding: 4px; border-radius: 9999px; display: flex; gap: 4px; border: 1px solid var(--gray); }}
        .tab-btn {{ background: none; border: none; color: #8b949e; padding: 0.5rem 1.5rem; border-radius: 9999px; cursor: pointer; font-size: 0.875rem; font-weight: 600; transition: 0.2s; }}
        .tab-btn.active {{ background: var(--primary); color: #fff; }}
        .kpi-row {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem; }}
        .kpi-card {{ background: var(--card); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--gray); text-align: center; }}
        .kpi-label {{ font-size: 0.75rem; font-weight: 600; color: #8b949e; margin-bottom: 0.5rem; }}
        .kpi-value {{ font-size: 2.25rem; font-weight: 700; color: #fff; }}
        .chart-card {{ background: var(--card); border-radius: 12px; border: 1px solid var(--gray); padding: 1.5rem; margin-bottom: 1.5rem; }}
        .chart-title {{ font-weight: 600; font-size: 1rem; color: #fff; margin-bottom: 1rem; }}
        .page {{ display: none; animation: fadeIn 0.4s ease; }}
        .page.active {{ display: block; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        .insight-box {{ background: rgba(88, 166, 255, 0.1); border-left: 4px solid var(--primary); padding: 1.25rem; border-radius: 4px; margin-top: 1.5rem; font-size: 0.95rem; color: #fff; }}
        footer {{ margin-top: 4rem; padding-top: 1.5rem; border-top: 1px solid var(--gray); text-align: center; font-size: 0.75rem; color: #8b949e; }}
        .modebar {{ display: none !important; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <header><h1>Sentiment & Spending Tracker Final</h1><div class="timestamp">Last Updated: {timestamp}</div></header>
        <div class="nav-container"><div class="pill-nav">
            <button class="tab-btn active" onclick="switchTab('p1', this)">Macro Overview</button>
            <button class="tab-btn" onclick="switchTab('p2', this)">Category Breakdown</button>
            <button class="tab-btn" onclick="switchTab('p3', this)">Income Segmentation</button>
        </div></div>
        <div id="p1" class="page active">
            <div class="kpi-row">
                <div class="kpi-card"><div class="kpi-label">Current Sentiment</div><div class="kpi-value">{current_sentiment:.1f}</div></div>
                <div class="kpi-card"><div class="kpi-label">Current 6m Divergence</div><div class="kpi-value" style="color: {get_color(current_div)}">{current_div:.2f}σ</div></div>
                <div class="kpi-card"><div class="kpi-label">12m Peak Abs Div</div><div class="kpi-value" style="color: {get_color(peak_12m_div)}">{peak_12m_div:.2f}σ</div></div>
            </div>
            <div class="chart-card"><div class="chart-title">Macro Sentiment vs. Spending Trends (Dual Axis)</div>
                {fig1.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})}
            </div>
        </div>
        <div id="p2" class="page">
            <div class="chart-card"><div class="chart-title">Growth Oscillations: Component Z-Scores</div>
                {fig2.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})}
            </div>
        </div>
        <div id="p3" class="page">
            <div class="chart-card"><div class="chart-title">Monthly Expenditures: Q1 vs Q5 ($)</div>
                {fig3_area.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})}
            </div>
            <div class="chart-card"><div class="chart-title">Q5/Q1 Spending Ratios</div>
                {fig3_bar.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})}
                <div class="insight-box">Highest-income households spend over 4x more than lowest-income households, with the widest gap in apparel and transportation.</div>
            </div>
        </div>
        <footer>Data Sources: FRED, BLS, University of Michigan</footer>
    </div>
    <script>
        function switchTab(id, el) {{
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            el.classList.add('active');
            window.dispatchEvent(new Event('resize'));
        }}
    </script>
</body>
</html>
"""

with open('sentiment_spending_dashboard_final.html', 'w') as f:
    f.write(html_content)

print("Final Dashboard created: sentiment_spending_dashboard_final.html")
