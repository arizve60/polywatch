import streamlit as st
import requests
import pandas as pd
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="Polymarket Whale Watcher", layout="wide")

# --- HEADERS ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0",
    "Accept": "application/json"
}

# --- FUNCTIONS ---
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

# --- DASHBOARD UI ---
st.title("🐳 Polymarket Live Whale Watcher")
st.markdown("Scan top traders in real-time to find active Copy Trading targets.")

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Scan Settings")

scan_depth = st.sidebar.slider("How many profiles to scan?", min_value=50, max_value=1000, value=100, step=50)
min_money = st.sidebar.number_input("Min Active Position ($)", value=50000, step=1000)
min_roi = st.sidebar.slider("Min ROI (%)", 0.0, 50.0, 1.0)
min_trades = st.sidebar.number_input("Min Markets Traded", value=50, step=10)

start_btn = st.sidebar.button("🚀 Start New Scan", type="primary")

# --- MAIN LOGIC ---
if start_btn:
    st.write(f"### 📡 Scanning Top {scan_depth} Traders...")
    
    # Progress Bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 1. Fetch Candidates
    base_url = "https://data-api.polymarket.com/v1/leaderboard"
    candidates = []
    pages = scan_depth // 50
    
    for i in range(pages):
        status_text.text(f"Downloading Leaderboard Page {i+1}/{pages}...")
        try:
            params = {"category": "OVERALL", "timePeriod": "MONTH", "orderBy": "PNL", "limit": 50, "offset": i*50}
            r = requests.get(base_url, params=params, headers=HEADERS)
            candidates.extend(r.json())
            time.sleep(0.1)
        except:
            pass
        progress_bar.progress((i + 1) / (pages * 2)) # Fill half bar during download

    # 2. Deep Scan
    final_traders = []
    total_candidates = len(candidates)
    
    table_placeholder = st.empty() # Placeholder to update table live
    
    for idx, trader in enumerate(candidates):
        wallet = trader.get('proxyWallet')
        
        # Update text status
        status_text.text(f"Scanning User {idx+1}/{total_candidates}: {trader.get('userName', 'Unknown')}")
        
        # Check 1: Experience
        trades = get_trade_count(wallet)
        if trades >= min_trades:
            
            # Check 2: Money (Slowest part)
            time.sleep(0.2) 
            val = get_manual_portfolio_value(wallet)
            
            if val >= min_money:
                
                # Check 3: ROI
                profit = float(trader.get('pnl', 0))
                vol = float(trader.get('vol', trader.get('volume', 0)))
                roi = (profit / vol * 100) if vol > 0 else 0
                
                if roi >= min_roi:
                    # Success!
                    name = trader.get('userName', 'Unnamed')
                    final_traders.append({
                        "Name": name,
                        "Active ($)": round(val, 2),
                        "ROI (%)": round(roi, 2),
                        "Profit ($)": round(profit, 2),
                        "Trades": trades,
                        "Wallet": wallet,
                        "Link": f"https://polymarket.com/profile/{wallet}"
                    })
                    
                    # LIVE UPDATE: Show table as we find them
                    if final_traders:
                        df_live = pd.DataFrame(final_traders)
                        df_live = df_live.sort_values(by="Active ($)", ascending=False)
                        table_placeholder.dataframe(df_live, use_container_width=True)

        # Update Progress
        progress_bar.progress(0.5 + (0.5 * (idx + 1) / total_candidates))

    status_text.success(f"✅ Scan Complete! Found {len(final_traders)} Whales.")
    
    # Final Table Display
    if final_traders:
        df = pd.DataFrame(final_traders)
        df = df.sort_values(by="Active ($)", ascending=False)
        
        # CSV Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Results CSV",
            data=csv,
            file_name="polymarket_live_whales.csv",
            mime="text/csv"
        )
    else:
        st.warning("No whales found matching your filters.")

else:
    st.info("👈 Adjust filters in the sidebar and click 'Start New Scan'")