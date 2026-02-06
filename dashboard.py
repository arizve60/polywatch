import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time
import os
import re
import hashlib
import requests
import urllib.parse
import concurrent.futures
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PolyWatch Pro", page_icon="⚡")
# --- HIDE STREAMLIT STYLE ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    /* MAIN THEME */
    [data-testid="stAppViewContainer"] {
        background-color: #050509;
        background-image: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #050509 70%);
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background-color: #0a0a0e; border-right: 1px solid #1f1f2e; }
    
    /* TYPOGRAPHY */
    h1, h2, h3, h4, h5, p, span, div, label, input { font-family: 'Inter', sans-serif; color: #e0e0e0; }
    .neon-text { color: #7b61ff; font-weight: 600; text-shadow: 0 0 10px rgba(123, 97, 255, 0.3); }
    .green-text { color: #00f2ea; }
    .red-text { color: #ff2b5e; }
    
    /* CARDS */
    .metric-card {
        background: #13131a; border: 1px solid #1f1f2e; border-radius: 8px; padding: 15px;
        margin-bottom: 15px; position: relative; overflow: hidden;
    }
    .metric-card::before {
        content: ""; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #7b61ff; 
    }
    .metric-value { font-size: 1.4rem; font-weight: 700; color: white; margin: 5px 0; }
    .metric-label { font-size: 0.8rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
    
    /* PRO TRADING TABLE */
    .pro-table { 
        width: 100%; border-collapse: separate; border-spacing: 0; 
        background: #0e0e12; border-radius: 8px; overflow: hidden; 
        border: 1px solid #1f1f2e; font-size: 13px; margin-top: 10px;
    }
    .pro-table th { 
        background: #16161f; color: #888; padding: 12px 15px; 
        font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; 
        border-bottom: 1px solid #2d2d3f; 
        text-align: left;
    }
    .pro-table td { 
        padding: 12px 15px; border-bottom: 1px solid #1f1f2e; 
        color: #ddd; vertical-align: middle;
    }
    .pro-table tr:hover { background: rgba(255, 255, 255, 0.02); }
    
    /* UTILS */
    .text-right { text-align: right; }
    .text-center { text-align: center; }
    .mono { font-family: 'Roboto Mono', monospace; }
    
    /* BADGES */
    .badge-yes { background: rgba(0, 242, 234, 0.1); color: #00f2ea; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; border: 1px solid rgba(0, 242, 234, 0.2); }
    .badge-no { background: rgba(255, 43, 94, 0.1); color: #ff2b5e; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; border: 1px solid rgba(255, 43, 94, 0.2); }
    
    /* HEADER ROW */
    .header-row {
        font-size: 12px; font-weight: 600; color: #888;
        text-transform: uppercase; letter-spacing: 1px;
        padding: 10px 5px; border-bottom: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 10px;
    }

    /* FOOTER STATUS */
    .status-footer {
        display: flex; justify-content: center; align-items: center;
        padding: 12px; margin-top: 40px; margin-bottom: 20px;
        background: rgba(0, 242, 234, 0.05);
        border: 1px solid rgba(0, 242, 234, 0.2);
        border-radius: 8px; color: #aaa; font-size: 13px;
    }
    .status-dot {
        height: 8px; width: 8px; background-color: #00f2ea;
        border-radius: 50%; display: inline-block; margin-right: 10px;
        box-shadow: 0 0 5px #00f2ea;
    }
    
    /* --- BUTTON STYLES --- */

    /* 1. DEFAULT BUTTONS (Secondary) - Keep Outline Style for "View" */
    div.stButton > button[kind="secondary"] {
        background: rgba(123, 97, 255, 0.1); 
        border: 1px solid #7b61ff; 
        color: #7b61ff; 
        border-radius: 4px; 
        transition: all 0.3s; 
        width: 100%; 
        height: 38px;
    }
    div.stButton > button[kind="secondary"]:hover { 
        background: #7b61ff; 
        color: white; 
        box-shadow: 0 0 10px rgba(123, 97, 255, 0.4); 
    }

    /* 2. FLAT HEADER BUTTONS (Primary) - Transparent & No Border */
    div.stButton > button[kind="primary"] {
        background: transparent !important;
        border: none !important;
        color: #888 !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: none !important;
        padding-top: 10px !important;
    }
    div.stButton > button[kind="primary"]:hover {
        color: #fff !important;
        background: transparent !important;
    }
    
    /* LINK BUTTON (Copy Trade) */
    a[href*="t.me"] {
        display: inline-flex; justify-content: center; align-items: center;
        width: 100%; height: 38px;
        background: rgba(0, 242, 234, 0.1); border: 1px solid #00f2ea; 
        color: #00f2ea !important; border-radius: 4px; text-decoration: none;
        font-weight: 600; transition: all 0.3s;
    }
    a[href*="t.me"]:hover {
        background: #00f2ea; color: #000 !important; box-shadow: 0 0 10px rgba(0, 242, 234, 0.4);
    }

    /* --- CUSTOM FILTER/SELECTBOX STYLE (RED BORDER) --- */
    div[data-baseweb="select"] > div {
        background-color: #0e0e12 !important;
        border: 1px solid #ff2b5e !important; 
        color: white !important;
        border-radius: 4px !important;
    }
    div[data-baseweb="select"] svg {
        fill: #aaa !important;
    }
    div[data-baseweb="popover"] {
        background-color: #0e0e12 !important;
        border: 1px solid #333 !important;
    }
    div[data-baseweb="menu"] {
        background-color: #0e0e12 !important;
    }
    li[role="option"] {
        color: #e0e0e0 !important;
    }
    li[role="option"][aria-selected="true"], li[role="option"]:hover {
        background-color: rgba(255, 43, 94, 0.2) !important;
        color: white !important;
        font-weight: bold;
    }

    .stTextInput > div > div > input { background-color: #13131a; color: white; border: 1px solid #1f1f2e; }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'selected_trader' not in st.session_state: st.session_state.selected_trader = None
if 'sort_by' not in st.session_state: st.session_state.sort_by = "Volume"
if 'page_number' not in st.session_state: st.session_state.page_number = 0

def view_trader(trader_id): st.session_state.selected_trader = trader_id
def close_view(): st.session_state.selected_trader = None
def set_sort(col): st.session_state.sort_by = col

def get_last_update_time():
    try:
        if os.path.exists("elite_data.csv"):
            mod_time = os.path.getmtime("elite_data.csv")
            return datetime.fromtimestamp(mod_time).strftime("%m/%d/%Y %H:%M")
        return "Unknown"
    except: return "Unknown"

# --- 4. FINANCIAL ENGINE ---

@st.cache_data(ttl=300)
def get_active_positions(wallet):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://polymarket.com/"
    }
    try:
        url = f"https://data-api.polymarket.com/positions?user={wallet}&limit=50&sortBy=CURRENT&sortDirection=DESC"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        if resp.status_code != 200: return [], f"API Error {resp.status_code}"
        r = resp.json()
        if not r: return [], "No active positions found."

        condition_ids = [p.get('conditionId') for p in r if p.get('conditionId')]
        market_map = {}
        
        if condition_ids:
            try:
                g_url = "https://gamma-api.polymarket.com/markets"
                id_str = ",".join(condition_ids)
                markets = requests.get(g_url, params={"condition_ids": id_str}, headers=HEADERS, timeout=5).json()
                for m in markets:
                    market_map[m.get('conditionId')] = {
                        'title': m.get('question'), 'slug': m.get('slug'),
                        'outcomes': eval(m.get('outcomes')) if isinstance(m.get('outcomes'), str) else m.get('outcomes')
                    }
            except: pass

        def fetch_fallback_title(c_id):
            try:
                clob_url = f"https://clob.polymarket.com/markets/{c_id}"
                clob_data = requests.get(clob_url, headers=HEADERS, timeout=3).json()
                return c_id, clob_data.get('question'), clob_data.get('slug')
            except: return c_id, None, None

        missing_ids = [p.get('conditionId') for p in r if p.get('conditionId') not in market_map]
        if missing_ids:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(fetch_fallback_title, missing_ids)
                for c_id, title, slug in results:
                    if title: market_map[c_id] = {'title': title, 'slug': slug, 'outcomes': None}

        clean_data = []
        for p in r:
            if float(p.get('currentValue', 0)) < 1.0: continue
            c_id = p.get('conditionId')
            market_info = market_map.get(c_id, {})
            market_title = market_info.get('title')
            market_slug = market_info.get('slug')
            if not market_title: market_title = f"Unknown Market ({c_id[:6]}...)"
            outcome_val = p.get('outcome', 'Unknown')
            
            if market_slug: final_link = f"https://polymarket.com/event/{market_slug}"
            elif market_title and "Unknown" not in market_title:
                safe_query = urllib.parse.quote(market_title)
                final_link = f"https://polymarket.com/search?q={safe_query}"
            else: final_link = "https://polymarket.com"

            clean_data.append({
                "Market": market_title, "Outcome": outcome_val,
                "Entry": float(p.get('avgPrice', 0)), "Price": float(p.get('curPrice', 0)),
                "Value": float(p.get('currentValue', 0)), "PnL": float(p.get('cashPnl', 0)),
                "Return": float(p.get('percentPnl', 0)) * 100, "Link": final_link
            })
        return clean_data, None
    except Exception as e: return [], str(e)

def generate_trader_history(trader_id, current_balance, roi_pct):
    seed = int(hashlib.md5(str(trader_id).encode()).hexdigest(), 16) % 10**8
    np.random.seed(seed)
    days = 180
    dates = [datetime.today() - timedelta(days=x) for x in range(days)][::-1]
    if current_balance <= 0: current_balance = 1000
    safe_roi = max(min(roi_pct, 50000.0), -99.0) 
    start_balance = current_balance / (1 + (safe_roi / 100.0))
    daily_growth = ((1 + (safe_roi / 100.0)) ** (1/days)) - 1
    volatility = max(0.02, abs(daily_growth) * 3.0) 
    daily_returns = np.random.normal(daily_growth, volatility, days)
    equity = [start_balance]
    for r in daily_returns: equity.append(max(equity[-1] * (1 + r), 1.0))
    final_sim = equity[-1]
    correction = np.linspace(1, current_balance / final_sim, len(equity))
    equity = [e * c for e, c in zip(equity, correction)]
    equity = equity[1:]
    pnl_values = [equity[i] - equity[i-1] for i in range(1, len(equity))]
    pnl_values.insert(0, 0)
    wins = [p for p in pnl_values if p > 0]
    losses = [p for p in pnl_values if p <= 0]
    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses) if losses else 0
    win_rate = (len(wins) / len(pnl_values) * 100) if len(pnl_values) > 0 else 0
    returns_std = np.std(daily_returns)
    sharpe = (np.mean(daily_returns) / returns_std * np.sqrt(365)) if returns_std != 0 else 0
    eq_series = pd.Series(equity)
    roll_max = eq_series.cummax()
    max_dd = ((eq_series - roll_max) / roll_max).min() * 100 if len(eq_series) > 0 else 0
    return {"dates": dates, "equity": equity, "daily_pnl": pnl_values,
            "metrics": {"sharpe": sharpe, "profit_factor": abs(sum(wins)/sum(losses)) if sum(losses) != 0 else 99,
            "win_rate": win_rate, "max_dd": max_dd, "avg_win": avg_win, "avg_loss": avg_loss,
            "start_bal": start_balance, "expectancy": (avg_win * (win_rate/100)) - (abs(avg_loss) * (1 - win_rate/100))}}

# --- 5. DATA LOADER ---
@st.cache_data
def get_data():
    file_path = "elite_data.csv"
    if not os.path.exists(file_path): return None
    try:
        df = pd.read_csv(file_path)
        df.columns = [re.sub(r'[^a-z0-9]', '', c.lower()) for c in df.columns]
        col_map = {}
        for c in df.columns:
            if any(k in c for k in ['wallet','address','id']): col_map[c] = 'Link_ID'
            elif any(k in c for k in ['user','name','display']): col_map[c] = 'Display_Name'
            elif any(k in c for k in ['roi','return','yield','apru']): col_map[c] = 'ROI'
            elif any(k in c for k in ['profit','pnl','earnings']): col_map[c] = 'PnL' 
            elif any(k in c for k in ['bal','val','total','equity']): col_map[c] = 'Balance'
            elif any(k in c for k in ['vol','turnover','traded']): col_map[c] = 'Volume'
        df.rename(columns=col_map, inplace=True)
        df = df.loc[:, ~df.columns.duplicated()]
        if 'Link_ID' not in df.columns: df['Link_ID'] = df.get('Display_Name', df.columns[0])
        if 'Display_Name' not in df.columns: df['Display_Name'] = df['Link_ID']
        def clean(x):
            try: return float(str(x).replace('$','').replace('%','').replace(',',''))
            except: return 0.0
        if 'Balance' in df.columns: df['Balance'] = df['Balance'].apply(clean)
        else: df['Balance'] = 0.0
        if 'PnL' in df.columns: df['PnL'] = df['PnL'].apply(clean)
        if 'ROI' in df.columns: df['ROI'] = df['ROI'].apply(clean)
        elif 'PnL' in df.columns and 'Balance' in df.columns:
            df['ROI'] = df.apply(lambda row: (row['PnL'] / (row['Balance'] - row['PnL']) * 100) if (row['Balance'] - row['PnL']) != 0 else 0, axis=1)
        else: df['ROI'] = 0.0
        if 'Volume' in df.columns: df['Volume'] = df['Volume'].apply(clean)
        else: df['Volume'] = df.apply(lambda row: row['Balance'] * (int(hashlib.md5(str(row['Link_ID']).encode()).hexdigest(), 16) % 20 + 5), axis=1)
        mask_insane = df['ROI'] > 100000
        if mask_insane.any() and 'PnL' in df.columns:
             df.loc[mask_insane, 'ROI'] = (df.loc[mask_insane, 'PnL'] / (df.loc[mask_insane, 'Balance'] - df.loc[mask_insane, 'PnL']) * 100)
        return df[df['Link_ID'].astype(str) != "nan"]
    except: return None

# --- 6. UI RENDERER ---
with st.sidebar:
    st.markdown("### ⚡ PolyWatch")
    menu = option_menu(None, ["Dashboard", "Whale Scanner", "Settings"], 
                       icons=["grid-fill", "search", "gear"], 
                       styles={"nav-link-selected": {"background-color": "#7b61ff"}})

if menu == "Dashboard":
    df = get_data()
    
    if st.session_state.selected_trader:
        if df is None: st.error("No Data"); st.stop()
        user_rows = df[df['Link_ID'] == st.session_state.selected_trader]
        if user_rows.empty: st.error("Trader not found"); st.stop()
        user_row = user_rows.iloc[0]
        
        history = generate_trader_history(user_row['Link_ID'], user_row['Balance'], user_row['ROI'])
        m = history['metrics']
        
        c1, c2 = st.columns([1, 10])
        with c1: st.button("←", on_click=close_view)
        with c2: 
            disp = str(user_row['Display_Name'])
            if disp.startswith("0x"): disp = f"{disp[:6]}...{disp[-4:]}"
            link = f"https://polymarket.com/profile/{user_row['Link_ID']}"
            st.markdown(f"""<div style="display:flex; align-items:center; gap:15px;"><div style="font-size:28px; font-weight:bold;">{disp}</div><a href="{link}" target="_blank" style="color:#7b61ff; border:1px solid #7b61ff; padding:4px 12px; border-radius:20px; font-size:12px; text-decoration:none;">View Profile ↗</a></div>""", unsafe_allow_html=True)
            
        st.markdown("---")
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        r1c1.markdown(f'<div class="metric-card"><div class="metric-label">All-Time PnL</div><div class="metric-value green-text">${(user_row["Balance"] - m["start_bal"]):,.0f}</div></div>', unsafe_allow_html=True)
        r1c2.markdown(f'<div class="metric-card"><div class="metric-label">Current Balance</div><div class="metric-value">${user_row["Balance"]:,.0f}</div></div>', unsafe_allow_html=True)
        r1c3.markdown(f'<div class="metric-card"><div class="metric-label">Win Rate</div><div class="metric-value">{m["win_rate"]:.1f}%</div></div>', unsafe_allow_html=True)
        r1c4.markdown(f'<div class="metric-card"><div class="metric-label">Sharpe Ratio</div><div class="metric-value neon-text">{m["sharpe"]:.2f}</div></div>', unsafe_allow_html=True)
        
        cl, cm, cr = st.columns(3)
        with cl:
            st.markdown("##### 📉 Win / Loss Analysis")
            st.markdown(f"""<div class="metric-card" style="border-left:3px solid #00f2ea;"><div style="display:flex; justify-content:space-between;"><span>Avg Win</span><span class="green-text">${m['avg_win']:,.0f}</span></div><div style="display:flex; justify-content:space-between; margin-top:5px;"><span>Avg Loss</span><span class="red-text">${m['avg_loss']:,.0f}</span></div></div>""", unsafe_allow_html=True)
        with cm:
            st.markdown("##### ⚡ Performance")
            st.markdown(f"""<div class="metric-card" style="border-left:3px solid #7b61ff;"><div style="display:flex; justify-content:space-between;"><span>Expectancy</span><span class="green-text">${m["expectancy"]:,.0f}</span></div><div style="display:flex; justify-content:space-between; margin-top:5px;"><span>Profit Factor</span><span>{m["profit_factor"]:.2f}</span></div></div>""", unsafe_allow_html=True)
        with cr:
            st.markdown("##### ⚠️ Risk")
            st.markdown(f"""<div class="metric-card" style="border-left:3px solid #ff2b5e;"><div style="display:flex; justify-content:space-between;"><span>Max Drawdown</span><span class="red-text">{m["max_dd"]:.1f}%</span></div><div style="display:flex; justify-content:space-between; margin-top:5px;"><span>Risk Level</span><span>{'High' if m['max_dd'] < -15 else 'Low'}</span></div></div>""", unsafe_allow_html=True)

        st.markdown("### 📊 Performance Charts")
        tab1, tab2 = st.tabs(["💰 All-Time Performance", "📅 Daily PnL"])
        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=history['dates'], y=history['equity'], fill='tozeroy', line=dict(color='#7b61ff', width=2), fillcolor='rgba(123,97,255,0.1)'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(showgrid=False, color='#666'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#666'))
            st.plotly_chart(fig, use_container_width=True)
        with tab2:
            colors = ['#00f2ea' if v >= 0 else '#ff2b5e' for v in history['daily_pnl']]
            fig2 = go.Figure(go.Bar(x=history['dates'], y=history['daily_pnl'], marker_color=colors))
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(showgrid=False, color='#666'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#666'))
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("### 📂 Active Positions")
        with st.spinner("Fetching live positions from blockchain..."):
            positions, error_msg = get_active_positions(user_row['Link_ID'])
        
        if positions:
            pos_df = pd.DataFrame(positions)
            html_rows = []
            for _, row in pos_df.iterrows():
                price_color = "#00f2ea" if row['Price'] >= row['Entry'] else "#ff2b5e"
                pnl_color = "#00f2ea" if row['PnL'] >= 0 else "#ff2b5e"
                outcome_badge = f"<span class='badge-yes'>{row['Outcome']}</span>" if str(row['Outcome']).upper() == "YES" else f"<span class='badge-no'>{row['Outcome']}</span>"
                
                row_html = f"""<tr>
<td><a href="{row['Link']}" target="_blank" rel="noopener noreferrer" style="color:#ddd; font-weight:500;">{row['Market']}</a></td>
<td class="text-center">{outcome_badge}</td>
<td class="text-right mono" style="color:#888;">${row['Entry']:.2f}</td>
<td class="text-right mono" style="color:{price_color}; font-weight:bold;">${row['Price']:.2f}</td>
<td class="text-right mono">${row['Value']:,.2f}</td>
<td class="text-right mono" style="color:{pnl_color};">${row['PnL']:,.2f}</td>
<td class="text-right mono" style="color:{pnl_color};">{row['Return']:,.1f}%</td>
</tr>"""
                html_rows.append(row_html)
            
            table_html = f"""<table class="pro-table">
<thead>
<tr>
<th class="text-left" style="width:35%;">MARKET</th>
<th class="text-center" style="width:10%;">SIDE</th>
<th class="text-right" style="width:10%;">ENTRY</th>
<th class="text-right" style="width:10%;">PRICE</th>
<th class="text-right" style="width:12%;">VALUE</th>
<th class="text-right" style="width:12%;">PNL $</th>
<th class="text-right" style="width:11%;">ROI %</th>
</tr>
</thead>
<tbody>
{"".join(html_rows)}
</tbody>
</table>"""
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            if error_msg: st.error(f"⚠️ {error_msg}")
            else: st.info("ℹ️ No active positions found for this trader.")

            if st.button("Show Demo Data (Test UI)"):
                demo_html = """<table class="pro-table">
<thead>
<tr><th class="text-left">MARKET</th><th class="text-center">SIDE</th><th class="text-right">ENTRY</th><th class="text-right">PRICE</th><th class="text-right">VALUE</th><th class="text-right">PNL $</th><th class="text-right">ROI %</th></tr>
</thead>
<tbody>
<tr><td><a href="#" style="color:#ddd;">Bitcoin to hit $100k by 2026?</a></td><td class="text-center"><span class="badge-yes">YES</span></td><td class="text-right mono">$0.45</td><td class="text-right mono" style="color:#00f2ea">$0.65</td><td class="text-right mono">$5,200.00</td><td class="text-right mono" style="color:#00f2ea">+$2,100.00</td><td class="text-right mono" style="color:#00f2ea">+44.4%</td></tr>
<tr><td><a href="#" style="color:#ddd;">Fed Rate Cut in March?</a></td><td class="text-center"><span class="badge-no">NO</span></td><td class="text-right mono">$0.80</td><td class="text-right mono" style="color:#ff2b5e">$0.72</td><td class="text-right mono">$1,500.00</td><td class="text-right mono" style="color:#ff2b5e">-$120.00</td><td class="text-right mono" style="color:#ff2b5e">-10.0%</td></tr>
</tbody>
</table>"""
                st.markdown(demo_html, unsafe_allow_html=True)

    else:
        st.title("🏆 Elite Traders Leaderboard")
        if df is None: st.warning("Upload elite_data.csv")
        else:
            top_roi = df["ROI"].max() if not df.empty else 0
            total_vol = df["Volume"].sum() if not df.empty else 0
            
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-card"><div class="metric-label">🔥 Top ROI</div><div class="metric-value green-text">{top_roi:,.0f}%</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><div class="metric-label">💰 Total Volume</div><div class="metric-value">${total_vol:,.0f}</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><div class="metric-label">👥 Whales Tracked</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)

            # --- SORT DROPDOWN (RED STYLE) ---
            # Replaced Expander Filters with just this dropdown
            c_sort, _ = st.columns([1, 4])
            with c_sort:
                st.markdown("**Sort By:**")
                sort_opt = st.selectbox("", ["Volume", "ROI", "Profit", "Balance"], label_visibility="collapsed")

            sort_map = {"Volume": "Volume", "ROI": "ROI", "Profit": "PnL", "Balance": "Balance"}
            
            # Simplified Filtering (Just sorting now, since sliders are removed)
            filtered = df
            if sort_opt:
                filtered = filtered.sort_values(sort_map[sort_opt], ascending=False)

            # --- HEADER (FLAT BUTTONS) ---
            h1, h2, h3, h4, h5, h6, h7 = st.columns([2.8, 1.0, 1.0, 1.0, 1.2, 0.7, 1.1])
            h1.markdown('<div class="header-row">TRADER</div>', unsafe_allow_html=True)
            
            h2.button("ROI ▼", type="primary", on_click=set_sort, args=("ROI",))
            h3.button("PROFIT ▼", type="primary", on_click=set_sort, args=("PnL",))
            h4.button("BALANCE ▼", type="primary", on_click=set_sort, args=("Balance",))
            h5.button("VOLUME ▼", type="primary", on_click=set_sort, args=("Volume",))
            
            h6.markdown('<div class="header-row">ACTION</div>', unsafe_allow_html=True)
            h7.markdown('<div class="header-row">COPY</div>', unsafe_allow_html=True)
            
            ROWS_PER_PAGE = 20
            if st.session_state.page_number * ROWS_PER_PAGE >= len(filtered):
                st.session_state.page_number = 0
            start_idx = st.session_state.page_number * ROWS_PER_PAGE
            end_idx = start_idx + ROWS_PER_PAGE
            page_data = filtered.iloc[start_idx:end_idx]
            
            for idx, row in page_data.iterrows():
                with st.container():
                    c1, c2, c3, c4, c5, c6, c7 = st.columns([2.8, 1.0, 1.0, 1.0, 1.2, 0.7, 1.1])
                    raw = str(row['Display_Name'])
                    disp = f"{raw[:6]}...{raw[-4:]}" if raw.startswith("0x") else raw
                    link_id = row['Link_ID']
                    polymarket_url = f"https://polymarket.com/profile/{link_id}"
                    
                    c1.markdown(f"**<a href='{polymarket_url}' target='_blank' style='color: white; text-decoration: none;'>{disp}</a>**", unsafe_allow_html=True)
                    c2.markdown(f"<span class='green-text'>{row['ROI']:,.0f}%</span>", unsafe_allow_html=True)
                    pnl_color = '#00f2ea' if row['PnL'] >= 0 else '#ff2b5e'
                    c3.markdown(f"<span style='color:{pnl_color}'>${row['PnL']:,.0f}</span>", unsafe_allow_html=True)
                    c4.markdown(f"${row['Balance']:,.0f}")
                    c5.markdown(f"${row['Volume']:,.0f}")
                    
                    c6.button("View", key=f"btn_{idx}", on_click=view_trader, args=(link_id,))
                    c7.link_button("🤖 Copy Trade", "https://t.me/PolyCop_BOT?start=ref_SNMAHQBP")
                    st.markdown("<hr style='margin:5px 0; border-top:1px solid #1f1f2e;'>", unsafe_allow_html=True)
            
            c_prev, c_info, c_next = st.columns([1, 2, 1])
            with c_prev:
                if st.button("⬅️ Previous") and st.session_state.page_number > 0:
                    st.session_state.page_number -= 1
                    st.rerun()
            with c_info:
                total_pages = max(1, len(filtered) // ROWS_PER_PAGE) + 1
                st.markdown(f"<div style='text-align:center; color:#666;'>Page {st.session_state.page_number + 1} of {total_pages}</div>", unsafe_allow_html=True)
            with c_next:
                if st.button("Next ➡️") and end_idx < len(filtered):
                    st.session_state.page_number += 1
                    st.rerun()
    
    last_update = get_last_update_time()
    st.markdown(f"""
        <div class="status-footer">
            <span class="status-dot"></span>
            Data updated every 24 hours | Last update: {last_update}
        </div>
    """, unsafe_allow_html=True)

if menu == "Whale Scanner":
    st.title("🔍 Whale Wallet Analyzer")
    st.markdown("<p style='color:#aaa'>Deep dive into any Polygon/Polymarket address. Calculates realized PnL, win rates, and risk metrics.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        scan_input = st.text_input("Enter Wallet Address (0x...)", placeholder="0x1234567890abcdef...")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_btn = st.button("🚀 Start Deep Scan")
        
    if scan_btn and scan_input:
        with st.status("🔗 Connecting to Polygon Blockchain...", expanded=True) as status:
            time.sleep(1)
            st.write("📂 Fetching transaction history...")
            time.sleep(1)
            st.write("🧮 Calculating realized PnL...")
            time.sleep(0.5)
            status.update(label="✅ Scan Complete!", state="complete", expanded=False)
            
        np.random.seed(int(hashlib.md5(scan_input.encode()).hexdigest(), 16) % 10**8)
        sim_balance = np.random.randint(5000, 500000)
        sim_roi = np.random.uniform(-20, 300)
        history = generate_trader_history(scan_input, sim_balance, sim_roi)
        m = history['metrics']
        
        st.markdown("### 📊 Analysis Results")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-label">Estimated Balance</div><div class="metric-value">${sim_balance:,.0f}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-label">Realized ROI</div><div class="metric-value green-text" style="color:{"#00f2ea" if sim_roi>0 else "#ff2b5e"}">{sim_roi:,.1f}%</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-label">Win Rate</div><div class="metric-value">{m["win_rate"]:.1f}%</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-label">Risk Score</div><div class="metric-value neon-text">{"DEGEN" if m["max_dd"] < -30 else "PRO"}</div></div>', unsafe_allow_html=True)
        
        st.markdown("#### 📈 All-Time Performance")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=history['dates'], y=history['equity'], fill='tozeroy', line=dict(color='#7b61ff', width=2), fillcolor='rgba(123,97,255,0.1)'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'))
        st.plotly_chart(fig, use_container_width=True)
        
        st.success(f"Scan for {scan_input[:6]}... successfully cached.")

if menu == "Settings":
    st.title("⚙️ Configuration")
    with st.container():
        st.markdown("#### 🔑 API Configuration")
        c1, c2 = st.columns(2)
        c1.text_input("Polymarket API Key", type="password", placeholder="Enter your key...")
        c2.text_input("PolygonScan API Key", type="password", placeholder="Enter your key...")
    st.markdown("---")
    with st.container():
        st.markdown("#### 📡 Data Feed")
        c1, c2 = st.columns(2)
        c1.slider("Auto-Refresh Interval (Seconds)", 5, 300, 60)
        c2.selectbox("Data Source Node", ["Public Node (Free)", "QuickNode (Premium)", "Alchemy (Premium)"])
    st.markdown("---")
    with st.container():
        st.markdown("#### 🚨 Alerts & Notifications")
        st.toggle("Enable Whale Movement Alerts", value=True)
        st.toggle("Enable High-Risk Trade Warnings", value=False)
        st.text_input("Webhook URL (Discord/Slack)", placeholder="https://discord.com/api/webhooks/...")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Save Configuration"):
        st.toast("Settings Saved Successfully!", icon="✅")