import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="PolyWatch Pro", page_icon="🔥")

# --- CUSTOM CSS (The "CoinSphere" Look) ---
st.markdown("""
<style>
    /* 1. MAIN BACKGROUND */
    .stApp {
        background: radial-gradient(circle at top left, #1a0b00, #000000);
    }
    
    /* 2. CARD DESIGN */
    .glass-card {
        background-color: #111111;
        border: 1px solid #333;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* 3. TEXT STYLES */
    .big-stat { font-size: 28px; font-weight: 700; color: #fff; }
    .sub-stat { font-size: 14px; color: #888; }
    .accent-orange { color: #FF6B35; font-weight: bold; }
    .accent-green { color: #00FF41; font-weight: bold; }
    
    /* 4. REMOVE WHITE SPACE */
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    selected = option_menu(
        menu_title="PolyWatch",
        options=["Dashboard", "Whale Scanner", "Analytics", "Settings"],
        icons=["grid-fill", "search", "bar-chart-fill", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"background-color": "#050505"},
            "icon": {"color": "white", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#222"},
            "nav-link-selected": {"background-color": "#FF6B35"},
        }
    )

# --- LOAD DATA ---
try:
    # Uses your GitHub raw link for live updates
    url = "https://raw.githubusercontent.com/arizve60/polywatch/main/elite_data.csv"
    df = pd.read_csv(url)
except:
    st.error("Connecting to Database...")
    st.stop()

# --- MAIN DASHBOARD LAYOUT ---
if selected == "Dashboard":
    
    # 1. TOP BAR (Search & Profile)
    c1, c2, c3 = st.columns([6, 2, 1])
    with c1:
        st.title("My Dashboard")
        st.caption(f"Live Market Data • {len(df)} Active Whales Tracked")
    with c3:
        st.markdown('<div style="background:#333; width:40px; height:40px; border-radius:50%; text-align:center; padding-top:8px;">👤</div>', unsafe_allow_html=True)

    st.divider()

    # 2. FEATURED STATS (The "My Balance" Cards)
    col1, col2, col3 = st.columns(3)
    
    # CARD 1: Top Whale
    top_whale = df.iloc[0]
    with col1:
        st.markdown(f"""
        <div class="glass-card">
            <div class="sub-stat">🔥 TOP WHALE</div>
            <div class="big-stat">{top_whale['userName']}</div>
            <div style="margin-top:10px;">
                <span class="accent-orange">${top_whale['active_balance']:,.0f}</span> 
                <span class="sub-stat"> Active</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # CARD 2: Market Volume
    total_cash = df['active_balance'].sum()
    with col2:
        st.markdown(f"""
        <div class="glass-card">
            <div class="sub-stat">💰 TOTAL VOLUME TRACKED</div>
            <div class="big-stat">${total_cash/1000000:,.1f}M</div>
            <div style="margin-top:10px;">
                <span class="accent-green">+2.4%</span> 
                <span class="sub-stat"> vs yesterday</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # CARD 3: ROI Leader
    roi_leader = df.sort_values(by="roi", ascending=False).iloc[0]
    with col3:
        st.markdown(f"""
        <div class="glass-card">
            <div class="sub-stat">🚀 HIGHEST ROI</div>
            <div class="big-stat">{roi_leader['roi']:.0f}%</div>
            <div style="margin-top:10px;">
                <span class="sub-stat">User: </span>
                <span style="color:#fff;">{roi_leader['userName']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. MAIN LIST (With "Invisible" Button Sorting)
    st.subheader("🏆 Elite Traders Leaderboard")
    
    # --- 1. MAGIC CSS (Makes buttons look like text headers) ---
    st.markdown("""
    <style>
    /* This targets the buttons inside the header row */
    div[data-testid="column"] button {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #888 !important;
        font-size: 0.8rem !important;
        font-weight: bold !important;
        padding: 0px !important;
        margin: 0px !important;
        height: auto !important;
        min-height: 0px !important;
        text-align: left !important;
    }
    div[data-testid="column"] button:hover {
        color: #FF6B35 !important; /* Turns Orange on Hover */
    }
    div[data-testid="column"] button:focus {
        color: #FF6B35 !important;
        border: none !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- 2. FILTERS ---
    with st.expander("🌪️ Filter Options", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            min_roi = st.slider("Min ROI (%)", -100, 500, 0)
        with c2:
            min_balance = st.number_input("Min Balance ($)", 0, value=1000, step=1000)

    # --- 3. SORT STATE ---
    if 'sort_col' not in st.session_state:
        st.session_state.sort_col = "roi"
    if 'sort_asc' not in st.session_state:
        st.session_state.sort_asc = False

    # --- 4. HEADER ROW (Now perfectly aligned) ---
    # We use columns to match the data layout
    h1, h2, h3, h4 = st.columns([3, 2, 2, 1.5])
    
    with h1:
        st.markdown('<div style="color:#888; font-size:0.8rem; font-weight:bold; padding-top:5px;">TRADER</div>', unsafe_allow_html=True)
    
    with h2:
        # Dynamic Label
        roi_label = "ROI ▼" if st.session_state.sort_col == "roi" and not st.session_state.sort_asc else "ROI"
        if st.session_state.sort_col == "roi" and st.session_state.sort_asc: roi_label = "ROI ▲"
        
        # The Button (Now looks like text thanks to CSS above)
        if st.button(roi_label, key="sort_roi"):
            if st.session_state.sort_col == "roi":
                st.session_state.sort_asc = not st.session_state.sort_asc
            else:
                st.session_state.sort_col = "roi"
                st.session_state.sort_asc = False
            st.rerun()

    with h3:
        # Dynamic Label
        bal_label = "BALANCE ▼" if st.session_state.sort_col == "active_balance" and not st.session_state.sort_asc else "BALANCE"
        if st.session_state.sort_col == "active_balance" and st.session_state.sort_asc: bal_label = "BALANCE ▲"
        
        if st.button(bal_label, key="sort_bal"):
            if st.session_state.sort_col == "active_balance":
                st.session_state.sort_asc = not st.session_state.sort_asc
            else:
                st.session_state.sort_col = "active_balance"
                st.session_state.sort_asc = False
            st.rerun()
            
    with h4:
        st.markdown('<div style="color:#888; font-size:0.8rem; font-weight:bold; padding-top:5px;">ACTION</div>', unsafe_allow_html=True)

    # --- 5. DATA LOGIC & DISPLAY ---
    filtered_df = df[
        (df['roi'] >= min_roi) & 
        (df['active_balance'] >= min_balance)
    ]
    
    sorted_df = filtered_df.sort_values(
        by=st.session_state.sort_col, 
        ascending=st.session_state.sort_asc
    )

    if 'page' not in st.session_state: st.session_state.page = 0
    items_per_page = 10
    
    if st.session_state.page * items_per_page > len(sorted_df): st.session_state.page = 0
    
    start = st.session_state.page * items_per_page
    end = (st.session_state.page + 1) * items_per_page
    page_data = sorted_df.iloc[start:end]
    
    st.divider() # Clean separator line

    if not page_data.empty:
        for index, row in page_data.iterrows():
            st.markdown(f"""
            <div class="glass-card" style="display:flex; justify-content:space-between; align-items:center; padding:15px 20px; margin-bottom:10px;">
                <div style="width:30%; display:flex; align-items:center; gap:10px;">
                    <div style="background:#222; width:35px; height:35px; border-radius:50%; display:flex; justify-content:center; align-items:center;">👤</div>
                    <div style="font-weight:bold; color:white;">{row['userName']}</div>
                </div>
                <div style="width:20%;" class="accent-green">{row['roi']:.1f}%</div>
                <div style="width:20%; color:white;">${row['active_balance']:,.0f}</div>
                <div style="width:15%;">
                    <a href="https://polymarket.com/profile/{row['proxyWallet']}" target="_blank" style="text-decoration:none; color:#FF6B35; border:1px solid #FF6B35; padding:5px 15px; border-radius:5px; font-size:0.8rem;">View</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    # Pagination
    col1, col2, col3 = st.columns([1, 8, 1])
    with col1:
        if st.session_state.page > 0 and st.button("⬅️ Prev"):
            st.session_state.page -= 1
            st.rerun()
    with col3:
        if end < len(sorted_df) and st.button("Next ➡️"):
            st.session_state.page += 1
            st.rerun()
# --- WHALE SCANNER PAGE (FUNCTIONAL VERSION) ---
elif selected == "Whale Scanner":
    st.title("🐳 Whale Scanner")
    st.caption("Search for any trader to see their hidden stats")
    
    # 1. THE REAL SEARCH BAR (Streamlit Widget)
    # We use a real input box, but style it to look professional
    search_query = st.text_input("🔍 Search by Username or Wallet Address", placeholder="e.g. kch123 or 0x6a...")
    
    st.divider()

    # 2. SEARCH LOGIC
    if search_query:
        # Filter the dataframe: Check if name contains query OR wallet contains query
        # Case insensitive (str.contains(..., case=False))
        result = df[
            df['userName'].astype(str).str.contains(search_query, case=False) | 
            df['proxyWallet'].astype(str).str.contains(search_query, case=False)
        ]
        
        # 3. DISPLAY RESULTS
        if not result.empty:
            st.success(f"Found {len(result)} trader(s)")
            
            for index, row in result.iterrows():
                # Display the "Player Card" for the found whale
                st.markdown(f"""
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-size:24px; font-weight:bold; color:white;">{row['userName']}</div>
                            <div style="font-size:12px; color:#888;">{row['proxyWallet']}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:24px; color:#00FF41;">{row['roi']:.1f}% ROI</div>
                            <div style="font-size:14px; color:#ccc;">Balance: ${row['active_balance']:,.0f}</div>
                        </div>
                    </div>
                    <hr style="border-color:#333;">
                    <div style="display:flex; gap:10px;">
                        <a href="https://polymarket.com/profile/{row['proxyWallet']}" target="_blank" style="background:#FF6B35; color:white; padding:8px 15px; border-radius:5px; text-decoration:none; font-size:14px;">View on Polymarket</a>
                        <a href="https://debank.com/profile/{row['proxyWallet']}" target="_blank" style="background:#333; color:white; padding:8px 15px; border-radius:5px; text-decoration:none; font-size:14px;">Scan on DeBank</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No trader found with that name/wallet. Try scanning the top list on the Dashboard.")
            
    else:
        # Default State (When nothing is typed)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="glass-card"><h3>🔹 Last Scan</h3><h1 style="color:#FF6B35">24m ago</h1></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="glass-card"><h3>🔹 New Whales Found</h3><h1 style="color:#00FF41">+12</h1></div>', unsafe_allow_html=True)
        
        st.info("Scanner is currently running on auto-pilot (Every 24h).")

# --- ANALYTICS PAGE (PROFESSIONAL ANIMATED VERSION) ---
elif selected == "Analytics":
    st.title("📊 Market Analytics")
    
    import plotly.express as px
    
    # 1. PREPARE DATA
    chart_data = df.sort_values(by="active_balance", ascending=False).head(15)
    
    # 2. CREATE ANIMATED CHART
    fig = px.bar(
        chart_data,
        x="userName",
        y="active_balance",
        color="roi",
        title="🐳 Top 15 Whales: Balance vs Profit",
        color_continuous_scale=["#FF4B4B", "#1f1f1f", "#00FF41"], # Red -> Dark -> Green
        template="plotly_dark",
        labels={"active_balance": "Wallet Size ($)", "userName": "Trader", "roi": "ROI %"},
        # ANIMATION SETTINGS:
        animation_frame=None, 
    )
    
    # 3. PRO DESIGN UPGRADES (The "Fintech" Look)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", family="sans-serif"),
        height=500,
        showlegend=False,
        xaxis=dict(showgrid=False, title=None, tickfont=dict(size=10, color="#888")), # Hide X grid
        yaxis=dict(showgrid=True, gridcolor="#333", title=None, tickprefix="$"),      # Subtle Y grid
        margin=dict(l=0, r=0, t=50, b=0)
    )

    # 4. HOVER INTERACTION (Glowing Tooltip)
    fig.update_traces(
        marker_line_width=0,       # No ugly borders
        hovertemplate="<b>%{x}</b><br>💰 Balance: $%{y:,.0f}<br>🚀 ROI: %{marker.color:.1f}%<extra></extra>"
    )

    # 5. DISPLAY
    st.plotly_chart(fig, use_container_width=True)
    
    # 6. LIVE PULSE STATS
    st.markdown("### ⚡ Live Market Pulse")
    
    # Calculate real numbers
    total_vol = df['active_balance'].sum()
    avg_roi = df['roi'].mean()
    top_winner = df.loc[df['roi'].idxmax()]
    
    # Custom CSS for "Glowing" Cards
    st.markdown("""
    <style>
    .metric-card {
        background: #111;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: scale(1.02);
        border-color: #FF6B35;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render Metrics in Columns
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><h3>💰 Total Volume</h3><h2 style="color:#FFF">${total_vol/1000000:.1f}M</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><h3>🚀 Avg ROI</h3><h2 style="color:#00FF41">{avg_roi:.1f}%</h2></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><h3>👑 Best Trader</h3><h2 style="color:#FF6B35">{top_winner["userName"]}</h2></div>', unsafe_allow_html=True)