import streamlit as st
import pandas as pd

# --- 1. PAGE SETUP ---
st.set_page_config(
    page_title="PolyScout // INSTANT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    
    /* CARD DESIGN */
    .trader-card {
        background: rgba(20, 20, 20, 0.6);
        border: 1px solid #333;
        border-radius: 12px;
        padding: 15px 25px;
        margin-bottom: 12px;
        transition: transform 0.2s, border-color 0.2s;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .trader-card:hover {
        transform: translateX(5px);
        border-color: #00ff41;
    }
    
    /* TEXT COLORS */
    .green-text { color: #00ff41 !important; font-weight: bold; }
    .white-text { color: #ffffff !important; font-weight: bold; }
    .grey-text { color: #888; font-size: 0.75rem; letter-spacing: 1px; text-transform: uppercase; }
    
    /* BUTTON */
    .analyze-btn {
        background: #111;
        border: 1px solid #444;
        color: #fff;
        padding: 8px 16px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.85rem;
        transition: 0.2s;
    }
    .analyze-btn:hover { border-color: #fff; background: #222; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOAD DATA ---
st.title("⚡ POLY SCOUT // ELITE FEED")

try:
    df = pd.read_csv("elite_data.csv")
except FileNotFoundError:
    st.error("⚠️ 'elite_data.csv' not found! You must run 'scanner.py' first.")
    st.stop()

# --- 4. FILTER BAR ---
with st.expander("🎛️ Live Filters (Refine Results)", expanded=True):
    c1, c2, c3 = st.columns(3)
    min_cash = c1.slider("Active Money ($)", 0, 500000, 50000)
    min_roi = c2.slider("Min ROI (%)", 0, 500, 5)
    sort_by = c3.selectbox("Sort By", ["Highest ROI", "Highest Active Cash", "Most Trades"])

# Apply Filters & Sorting
filtered_df = df[ (df['active_balance'] >= min_cash) & (df['roi'] >= min_roi) ]

if sort_by == "Highest ROI":
    filtered_df = filtered_df.sort_values(by="roi", ascending=False)
elif sort_by == "Highest Active Cash":
    filtered_df = filtered_df.sort_values(by="active_balance", ascending=False)
else:
    filtered_df = filtered_df.sort_values(by="trade_count", ascending=False)

# --- 5. PAGINATION (THE NEW PART) ---
st.divider()

if len(filtered_df) > 0:
    # A. Calculate total pages
    items_per_page = 20
    total_items = len(filtered_df)
    total_pages = max(1, (total_items - 1) // items_per_page + 1)
    
    # B. Show Page Selector
    col_left, col_right = st.columns([1, 4])
    with col_left:
        current_page = st.number_input("Page Number", min_value=1, max_value=total_pages, value=1)
    with col_right:
        st.write("") # Spacer
        st.write("") 
        st.caption(f"Showing Page {current_page} of {total_pages} (Total: {total_items} Traders)")

    # C. Slice the Data
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_data = filtered_df.iloc[start_idx:end_idx]

    # --- 6. DISPLAY CARDS ---
    for index, row in page_data.iterrows():
        name = row.get('userName', 'Unknown')
        wallet = row.get('proxyWallet')
        roi = row['roi']
        active = row['active_balance']
        trades = row['trade_count']
        
        # Calculate Rank (Global Rank)
        # If you are on page 2, the first person is Rank #21
        global_rank = start_idx + list(page_data.index).index(index) + 1
        
        html = f"""
<div class="trader-card">
<div style="display:flex; align-items:center; gap:15px; width:30%;">
<span style="font-size:1.2rem; font-weight:bold; color:#444;">#{global_rank}</span>
<div style="background:#222; width:45px; height:45px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.2rem;">👤</div>
<div>
<h3 style="margin:0; font-size:1.1rem; color:#fff;">{name}</h3>
<p style="margin:0; font-size:0.8rem; color:#666;">{trades} Trades</p>
</div>
</div>
<div style="display:flex; gap:40px; width:40%;">
<div>
<div class="grey-text">ROI (30d)</div>
<div class="green-text" style="font-size:1.2rem;">{roi:.1f}%</div>
</div>
<div>
<div class="grey-text">ACTIVE CASH</div>
<div class="white-text" style="font-size:1.2rem;">${active:,.0f}</div>
</div>
</div>
<div style="width:20%; text-align:right;">
<a href="https://polymarket.com/profile/{wallet}" target="_blank" class="analyze-btn">
Analyze ↗
</a>
</div>
</div>
"""
        st.markdown(html, unsafe_allow_html=True)

else:
    st.warning("No traders match these filters. Try lowering the sliders!")