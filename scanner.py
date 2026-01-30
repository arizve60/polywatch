import requests
import pandas as pd
import time

# --- 1. YOUR SETTINGS (Exact Logic) ---
SCAN_LIMIT = 1000       # <--- REQ 1: Top 1000 Profiles
MIN_ACTIVE = 50000      # <--- REQ 2: Open Positions > $50k
MIN_TRADES = 100        # <--- REQ 4: Experience > 100 Trades
MIN_ROI = 1.0           # <--- REQ 3: ROI > 1%

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_trade_count(wallet):
    try:
        r = requests.get(f"https://data-api.polymarket.com/traded?user={wallet}", headers=HEADERS)
        return int(r.json().get('traded', 0))
    except:
        return 0

def get_active_balance(wallet):
    try:
        r = requests.get(f"https://data-api.polymarket.com/positions?user={wallet}", headers=HEADERS)
        data = r.json()
        return sum([float(p.get('currentValue', 0)) for p in data])
    except:
        return 0.0

def run_scan():
    print(f"🚀 Starting Scan of top {SCAN_LIMIT} profiles...")
    print(f"   Filters: >${MIN_ACTIVE} Active | >{MIN_TRADES} Trades | >{MIN_ROI}% ROI")
    
    base_url = "https://data-api.polymarket.com/v1/leaderboard"
    elite_survivors = []
    
    # Calculate pages: 1000 people / 50 per page = 20 Pages
    pages = SCAN_LIMIT // 50
    
    for i in range(pages):
        print(f"📄 Scanning Page {i+1}/{pages}...")
        try:
            # Fetches the top monthly traders (sorted by PnL)
            params = {"category": "OVERALL", "timePeriod": "MONTH", "orderBy": "PNL", "limit": 50, "offset": i*50}
            batch = requests.get(base_url, params=params, headers=HEADERS).json()
            
            for trader in batch:
                wallet = trader.get('proxyWallet')
                
                # --- LOGIC CHECK 1: TRADES > 100 ---
                trades = get_trade_count(wallet)
                if trades >= MIN_TRADES:
                    
                    # Be polite to API (prevents crashing)
                    time.sleep(0.1) 
                    
                    # --- LOGIC CHECK 2: ACTIVE CASH > $50k ---
                    active = get_active_balance(wallet)
                    if active >= MIN_ACTIVE:
                        
                        # --- LOGIC CHECK 3: ROI > 1% ---
                        profit = float(trader.get('pnl', 0))
                        vol = float(trader.get('vol', trader.get('volume', 0)))
                        
                        # Formula: (Profit / Volume) * 100
                        roi = (profit / vol * 100) if vol > 0 else 0
                        
                        if roi >= MIN_ROI:
                            userName = trader.get('userName') or "Unknown"
                            print(f"✅ FOUND WHALE: {userName} (Active: ${active:,.0f} | ROI: {roi:.1f}%)")
                            
                            # Add to the "Survivors" list
                            trader['active_balance'] = active
                            trader['trade_count'] = trades
                            trader['roi'] = roi
                            elite_survivors.append(trader)
                            
        except Exception as e:
            print(f"Error on page {i}: {e}")

    # Save results to CSV
    if elite_survivors:
        df = pd.DataFrame(elite_survivors)
        df.to_csv("elite_data.csv", index=False)
        print(f"🎉 SUCCESS! Saved {len(elite_survivors)} whales to 'elite_data.csv'")
    else:
        print("❌ No traders matched your strict filters.")

if __name__ == "__main__":
    run_scan()