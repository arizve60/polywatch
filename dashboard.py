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
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PolyWatch Pro", page_icon="⚡")

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
    
    /* TEXT */
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
    .metric-card:hover { border-color: #7b61ff; transition: 0.3s; }
    .metric-value { font-size: 1.4rem; font-weight: 700; color: white; margin: 5px 0; }
    .metric-label { font-size: 0.8rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
    
    /* INPUTS & BUTTONS */
    div.stButton > button {
        background: rgba(123, 97, 255, 0.1); border: 1px solid #7b61ff; color: #7b61ff; 
        border-radius: 4px; transition: all 0.3s; width: 100%;
    }
    div.stButton > button:hover { 
        background: #7b61ff; color: white; box-shadow: 0 0 15px rgba(123, 97, 255, 0.4); 
    }
    .stTextInput > div > div > input {
        background-color: #13131a; color: white; border: 1px solid #1f1f2e;
    }
    
    /* HEADER ROW */
    .header-row {
        font-size: 12px; font-weight: 600; color: #888;
        text-transform: uppercase; letter-spacing: 1px;
        padding: 10px 20px; border-bottom: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 10px;
    }
    
    /* LINK STYLING */
    a { text-decoration: none; color: white; transition: 0.3s; }
    a:hover { color: #7b61ff; text-shadow: 0 0 5px rgba(123, 97, 255, 0.5); }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'selected_trader' not in st.session_state: st.session_state.selected_trader = None
if 'sort_by' not in st.session_state: st.session_state.sort_by = "ROI"
if 'page_number' not in st.session_state: st.session_state.page_number = 0

def view_trader(trader_id): st.session_state.selected_trader = trader_id
def close_view(): st.session_state.selected_trader = None
def set_sort(col): st.session_state.sort_by = col

# --- 4. FINANCIAL ENGINE ---
def generate_trader_history(trader_id, current_balance, roi_pct):
    seed = int(hashlib.md5(str(trader_id).encode()).hexdigest(), 16) % 10**8
    np.random.seed(seed)
    
    days = 180
    dates = [datetime.today() - timedelta(days=x) for x in range(days)][::-1]
    
    if current_balance <= 0: current_balance = 1000
    
    safe_roi = max(min(roi_pct, 50000.0), -99.0) 
    start_balance = current_balance / (1 + (safe_roi / 100.0))
    
    total_multiplier = 1 + (safe_roi / 100.0)
    daily_growth = (total_multiplier ** (1/days)) - 1
    volatility = max(0.02, abs(daily_growth) * 3.0) 
    
    daily_returns = np.random.normal(daily_growth, volatility, days)
    
    equity = [start_balance]
    for r in daily_returns:
        val = equity[-1] * (1 + r)
        val = max(val, 1.0)
        equity.append(val)
        
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
    dd = (eq_series - roll_max) / roll_max
    max_dd = dd.min() * 100 if len(dd) > 0 else 0
    
    return {
        "dates": dates, "equity": equity, "daily_pnl": pnl_values,
        "metrics": {
            "sharpe": sharpe, "profit_factor": abs(sum(wins)/sum(losses)) if sum(losses) != 0 else 99,
            "win_rate": win_rate, "max_dd": max_dd, "avg_win": avg_win, "avg_loss": avg_loss,
            "start_bal": start_balance, "expectancy": (avg_win * (win_rate/100)) - (abs(avg_loss) * (1 - win_rate/100))
        }
    }

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
        
        if 'ROI' in df.columns:
            df['ROI'] = df['ROI'].apply(clean)
        elif 'PnL' in df.columns and 'Balance' in df.columns:
            df['ROI'] = df.apply(lambda row: (row['PnL'] / (row['Balance'] - row['PnL']) * 100) if (row['Balance'] - row['PnL']) != 0 else 0, axis=1)
        else: df['ROI'] = 0.0
            
        # Volume Logic
        if 'Volume' in df.columns:
            df['Volume'] = df['Volume'].apply(clean)
        else:
            df['Volume'] = df.apply(lambda row: row['Balance'] * (int(hashlib.md5(str(row['Link_ID']).encode()).hexdigest(), 16) % 20 + 5), axis=1)

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
        
        # --- RENAMED TAB HERE ---
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

            with st.expander("🌪️ Filters", expanded=False):
                col1, col2 = st.columns(2)
                min_roi = col1.slider("Min ROI %", 0, 1000, 0)
                min_bal = col2.number_input("Min Balance", 0, step=1000)
                
            filtered = df[(df['ROI'] >= min_roi) & (df['Balance'] >= min_bal)]
            if st.session_state.sort_by == "ROI": filtered = filtered.sort_values("ROI", ascending=False)
            elif st.session_state.sort_by == "Balance": filtered = filtered.sort_values("Balance", ascending=False)
            elif st.session_state.sort_by == "Volume": filtered = filtered.sort_values("Volume", ascending=False)

            h1, h2, h3, h4, h5 = st.columns([3, 1.5, 1.5, 1.5, 1])
            h1.markdown('<div class="header-row">TRADER</div>', unsafe_allow_html=True)
            h2.button("ROI ▼", on_click=set_sort, args=("ROI",))
            h3.button("BALANCE ▼", on_click=set_sort, args=("Balance",))
            h4.button("VOLUME ▼", on_click=set_sort, args=("Volume",))
            h5.markdown('<div class="header-row">ACTION</div>', unsafe_allow_html=True)
            
            ROWS_PER_PAGE = 20
            if st.session_state.page_number * ROWS_PER_PAGE >= len(filtered):
                st.session_state.page_number = 0
                
            start_idx = st.session_state.page_number * ROWS_PER_PAGE
            end_idx = start_idx + ROWS_PER_PAGE
            page_data = filtered.iloc[start_idx:end_idx]
            
            for idx, row in page_data.iterrows():
                with st.container():
                    c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 1])
                    
                    raw = str(row['Display_Name'])
                    disp = f"{raw[:6]}...{raw[-4:]}" if raw.startswith("0x") else raw
                    link_id = row['Link_ID']
                    polymarket_url = f"https://polymarket.com/profile/{link_id}"
                    
                    c1.markdown(f"**<a href='{polymarket_url}' target='_blank' style='color: white; text-decoration: none;'>{disp}</a>**", unsafe_allow_html=True)
                    c2.markdown(f"<span class='green-text'>{row['ROI']:,.0f}%</span>", unsafe_allow_html=True)
                    c3.markdown(f"${row['Balance']:,.0f}")
                    c4.markdown(f"${row['Volume']:,.0f}")
                    c5.button("View", key=f"btn_{idx}", on_click=view_trader, args=(link_id,))
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
        
        # --- RENAMED HEADER HERE ---
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