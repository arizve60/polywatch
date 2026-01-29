import streamlit as st
import requests
import pandas as pd
import time

# --- 1. PAGE CONFIGURATION (Must be first) ---
st.set_page_config(
    page_title="PolyWatch Pro",
    page_icon="🐳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (To make it look fancy) ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #4CAF50; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADERS ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0",
    "Accept": "application/json"
}

# --- HELPER FUNCTIONS ---
def get_trade_count(wallet_address):
    try:
        url = "https://data-api.polymarket.com/traded"
        params = {"user": wallet_address}
        response = requests.get(url, params=params, headers=HEADERS)
        if response.status_code == 200:
            return int(response.json().get('traded', 0))
        return 0
    except:
        return 0

def get_manual_portfolio_value(wallet_address):
    try:
        url = "https://data-api.polymarket.com/positions"
        params = {"user": wallet_address}
        response = requests.get(url, params=params, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            total = sum([float(p.get('currentValue', 0)) for p in data])
            return total
        return 0.0
    except:
        return 0.0

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("🎛️ Control Panel")
    st.write("Configure your scanning filters below.")
    
    st.divider()
    
    scan_depth = st.slider("📡 Scan Depth (Profiles)", 50, 1000, 100, 50)
    min_money = st.number_input("💰 Min Active Capital ($)", value=50000, step=5000)
    min_roi = st.slider("📈 Min ROI (%)", 0.0, 100.0, 1.0)
    min_trades = st.number_input("🧠 Min Trades (Experience)", value=50, step=10)
    
    st.divider()
    start_btn = st.button("🚀 LAUNCH SCANNER", type="primary", use_container_width=True)

# --- MAIN DASHBOARD UI ---
st.title("🐳 PolyWatch Pro Dashboard")
st.markdown("Real-time arbitrage & copy-trading intelligence.")

# TABS LAYOUT
tab1, tab2 = st.tabs(["📊 Live Scanner", "ℹ️ How it Works"])

with tab1:
    # Top Metrics Row (Empty at first)
    col1, col2, col3, col4 = st.columns(4)
    metric_count = col1.metric("Whales Found", "0")
    metric_money = col2.metric("Total Active Cap", "$0")
    metric_roi = col3.metric("Top ROI", "0%")
    metric_status = col4.metric("Status", "Idle")

    st.divider()

    # Placeholders for data
    progress_bar = st.progress(0)
    table_placeholder = st.empty()

    if start_btn:
        metric_status.metric("Status", "Scanning...", delta_color="off")
        
        # 1. Fetch Candidates
        base_url = "https://data-api.polymarket.com/v1/leaderboard"
        candidates = []
        pages = scan_depth // 50
        
        for i in range(pages):
            try:
                params = {"category": "OVERALL", "timePeriod": "MONTH", "orderBy": "PNL", "limit": 50, "offset": i*50}
                r = requests.get(base_url, params=params, headers=HEADERS)
                candidates.extend(r.json())
                time.sleep(0.1)
            except:
                pass
            # Update bar during download
            progress_bar.progress((i + 1) / (pages * 2))

        # 2. Deep Scan
        final_traders = []
        total_candidates = len(candidates)
        
        # Variables for metrics
        top_roi_seen = 0.0
        total_money_seen = 0.0
        
        for idx, trader in enumerate(candidates):
            wallet = trader.get('proxyWallet')
            
            # Check Experience
            trades = get_trade_count(wallet)
            if trades >= min_trades:
                
                # Check Money
                time.sleep(0.2) 
                val = get_manual_portfolio_value(wallet)
                
                if val >= min_money:
                    
                    # Check ROI
                    profit = float(trader.get('pnl', 0))
                    vol = float(trader.get('vol', trader.get('volume', 0)))
                    roi = (profit / vol * 100) if vol > 0 else 0
                    
                    if roi >= min_roi:
                        # SUCCESS - Add to list
                        name = trader.get('userName', 'Unnamed')
                        
                        # Update Metrics Variables
                        if roi > top_roi_seen: top_roi_seen = roi
                        total_money_seen += val
                        
                        final_traders.append({
                            "Name": name,
                            "Active Capital ($)": val,
                            "ROI (%)": roi,
                            "Monthly Profit ($)": profit,
                            "Experience (Trades)": trades,
                            "Link": f"https://polymarket.com/profile/{wallet}"
                        })
                        
                        # LIVE UI UPDATE
                        metric_count.metric("Whales Found", f"{len(final_traders)}")
                        metric_money.metric("Total Active Cap", f"${total_money_seen/1000000:.1f}M")
                        metric_roi.metric("Top ROI", f"{top_roi_seen:.1f}%")
                        
                        # Live Table
                        if final_traders:
                            df = pd.DataFrame(final_traders)
                            # Sort
                            df = df.sort_values(by="Active Capital ($)", ascending=False)
                            
                            # STYLING: Highlight big numbers
                            st.dataframe(
                                df,
                                column_config={
                                    "Link": st.column_config.LinkColumn("Profile"),
                                    "Active Capital ($)": st.column_config.NumberColumn(format="$%.2f"),
                                    "Monthly Profit ($)": st.column_config.NumberColumn(format="$%.2f"),
                                    "ROI (%)": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                                },
                                use_container_width=True
                            )

            # Update Progress
            progress_bar.progress(0.5 + (0.5 * (idx + 1) / total_candidates))

        metric_status.metric("Status", "Complete", delta_color="normal")
        
        if final_traders:
            st.success(f"Scan Finished! Found {len(final_traders)} elite traders.")
            # CSV Download
            df = pd.DataFrame(final_traders)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Data as CSV", csv, "polywatch_pro.csv", "text/csv")
        else:
            st.warning("No traders found. Try lowering your filters.")

with tab2:
    st.markdown("""
    ### ℹ️ How to use PolyWatch Pro
    
    1.  **Set Scan Depth:** Higher means more results, but slower speed.
    2.  **Min Active Capital:** Only finds people risking real money RIGHT NOW.
    3.  **Min Trades:** Filters out lucky beginners.
    
    **Tips:**
    * Look for High ROI + High Experience.
    * Click the **Profile Link** in the table to see exactly what they are betting on.
    """)